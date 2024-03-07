import os
import uuid
from gai.common.errors import DuplicatedDocumentException
from gai.gen.rag.dalc.IndexedDocumentChunk import IndexedDocumentChunk
from gai.gen.rag.dalc.IndexedDocumentChunkGroup import IndexedDocumentChunkGroup
from gai.gen.rag.models.ChunkInfoPydantic import ChunkInfoPydantic
from gai.gen.rag.models.IndexedDocumentChunkGroupPydantic import IndexedDocumentChunkGroupPydantic
from gai.gen.rag.models.IndexedDocumentHeaderPydantic import IndexedDocumentHeaderPydantic
from gai.gen.rag.models.IndexedDocumentPydantic import IndexedDocumentPydantic
from tqdm import tqdm
from datetime import datetime
from datetime import date
from sqlalchemy import MetaData, create_engine
from sqlalchemy.orm import sessionmaker, selectinload, defer
from gai.gen.rag.dalc.Base import Base
from gai.common.utils import get_gen_config, get_app_path
from gai.common import logging, file_utils
from gai.common.PDFConvert import PDFConvert
from gai.gen.rag.dalc.IndexedDocument import IndexedDocument
logger = logging.getLogger(__name__)

class RAGDBRepository:

    @staticmethod
    def New(in_memory=False):
        try:
            config = get_gen_config()["gen"]["rag"]
            app_path = get_app_path()
            sqlite_path = os.path.join(app_path, config["sqlite"]["path"])
            sqlite_string = f'sqlite:///{sqlite_path}'
            if in_memory:
                sqlite_string = 'sqlite:///:memory:'
            logger.info(f"RAGDBRepository: sqlite_path={sqlite_string}")
            engine = create_engine(sqlite_string)

            # Create the database if it doesn't exist
            Base.metadata.create_all(engine)

            return RAGDBRepository(engine)
        except Exception as e:
            if not "does not exist." in str(e):
                raise e
    
    def __init__(self,engine):
        self.config = get_gen_config()["gen"]["rag"]
        self.app_path = get_app_path()
        self.chunks_path = os.path.join(self.app_path, self.config["chunks"]["path"])
        self.chunk_size = self.config["chunks"]["size"]
        self.chunk_overlap = self.config["chunks"]["overlap"]
        self.engine = engine
        self.db_path = str(self.engine.url).split("///")[-1]
        if self.db_path == ":memory:":
            self.db_path = None
        if not self.engine.url.startswith("sqlite"):
            raise ValueError("Only sqlite databases are supported")

# Indexing Transaction -------------------------------------------------------------------------------------------------------------------------------------------

    '''
    This function will either load a PDF file or text file into memory.
    '''
    def _load_and_convert(self, file_path, file_type=None):
        if file_type is None:
            file_type = file_path.split('.')[-1]
        if file_type == 'pdf':
            text = PDFConvert.pdf_to_text(file_path)
        elif file_type == 'txt':
            with open(file_path, 'r') as f:
                text = f.read()
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        return text

    '''
    Used to get document_id from content
    '''
    def create_document_hash(self, collection_name, file_path):
        session = sessionmaker(bind=self.engine)()
        if not session:
            raise ValueError("RAGDBRepository.create_document_hash: Session is required.")

        text = self._load_and_convert(file_path)
        document_id = file_utils.create_chunk_id_base64(text)
        try:
            found = session.query(IndexedDocument).filter(IndexedDocument.Id==document_id, IndexedDocument.CollectionName==collection_name).first()
            if found is not None:
                raise ValueError(f"Document already exists in the database: {document_id}")
            return document_id
        except:
            raise

    def _create_document_hash(self, collection_name, file_path, session):
        session = sessionmaker(bind=self.engine)()
        if not session:
            raise ValueError("RAGDBRepository.create_document_hash: Session is required.")

        text = self._load_and_convert(file_path)
        document_id = file_utils.create_chunk_id_base64(text)
        try:
            found = session.query(IndexedDocument).filter(IndexedDocument.Id==document_id, IndexedDocument.CollectionName==collection_name).first()
            if found is not None:
                raise DuplicatedDocumentException(f"Document already exists in the database: {document_id}")
            return document_id
        except Exception as e:
            logger.error(f"RAGDBRepository._create_document_hash: Error={str(e)}")
            raise

    '''
    This will create a document header and generate the document ID.
    The document header is the original source and is decoupled from the chunks.
    This is because there will be many different ways of splitting the document into chunks but the source will remain the same.
    It is also possible that the document may be deactivated from the semantic search and when that is the case, all chunk groups
    (as well as the chunks under each group) will be deactivated as well.
    '''
    def create_document_header(self,
        collection_name,
        file_path,
        file_type,
        title=None,
        source=None,
        abstract=None,
        authors=None,
        publisher=None,
        published_date=None,
        comments=None,
        keywords=None,
        session=None
        ):

        try:
            if not session:
                raise ValueError("RAGDBRepository.create_document_header: Session is required.")

            document = IndexedDocument()

            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
           
            doc_id = self._create_document_hash(collection_name, file_path, session)

            document.Id = doc_id       
            document.FileName = os.path.basename(file_path)
            document.FileType = file_type
            document.ByteSize = os.path.getsize(file_path)
            document.CollectionName = collection_name
            document.Title = title
            document.Source = source
            document.Abstract = abstract
            document.Authors = authors
            document.Publisher = publisher
            document.PublishedDate = published_date
            document.Comments = comments
            document.Keywords = keywords
            document.IsActive = True
            document.CreatedAt = datetime.now()
            document.UpdatedAt = datetime.now()

            # Assuming document.PublishedDate could be either a string or a datetime.date object
            if isinstance(document.PublishedDate, str):
                try:
                    # Correct the date format to match the input, e.g., '2017-June-12'
                    document.PublishedDate = datetime.strptime(document.PublishedDate, '%Y-%B-%d').date()
                except ValueError:
                    # Log the error or handle it as needed
                    document.PublishedDate = None
            elif not isinstance(document.PublishedDate, date):
                document.PublishedDate = None

            # Read the file content
            with open(file_path, 'rb') as f:
                document.File = f.read()
            
            session.add(document)

            pydantic_document = IndexedDocumentPydantic.from_orm(document)

            return pydantic_document
        except Exception as e:
            logger.error(f"RAGDBRepository.create_document_header: Error={str(e)}")
            raise

    '''
    There are many ways that a document can be chunked based on different strategies such as chunk size, overlap, algorithm, etc.
    This function will create a chunk group and then create the chunks in chunks_dir based on the strategy.
    '''
    def create_chunkgroup(self, doc_id, chunk_size, chunk_overlap, splitter, session):
        try:
            # Load text from database or load text converted from pdf from database
            document = session.query(IndexedDocument).filter_by(Id=doc_id).first()
            if document is None:
                raise ValueError(f"RAGDBRepository.create_chunkgroup: Document header not found {doc_id}")
            
            if document.FileType == 'pdf':
                import tempfile
                with tempfile.NamedTemporaryFile() as temp_file:
                    temp_file.write(document.File)
                    temp_file_path = temp_file.name
                    text = PDFConvert.pdf_to_text(temp_file_path)
            elif document.FileType == 'txt':
                text = document.File.decode('utf-8')
            else:
                raise ValueError(f"Unsupported file type: {document.FileType}")
            
            # Write the text into a temp text file
            filename = ".".join(document.FileName.split(".")[:-1])
            src_file = f"/tmp/{filename}.txt"
            with open(src_file, 'w') as f:
                f.write(text)

            #Split temp text file into chunks and save into chunks_dir
            if chunk_size is None:
                chunk_size = self.chunk_size
            if chunk_overlap is None:
                chunk_overlap = self.chunk_overlap
            chunks_dir = splitter(src_file=src_file, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks_count = len(os.listdir(chunks_dir))

            chunkgroup = IndexedDocumentChunkGroup()
            chunkgroup.Id = str(uuid.uuid4())
            chunkgroup.DocumentId = doc_id
            chunkgroup.SplitAlgo = "recursive_split"
            chunkgroup.ChunkCount = chunks_count
            chunkgroup.ChunkSize = chunk_size
            chunkgroup.Overlap = chunk_overlap
            chunkgroup.IsActive = True
            chunkgroup.ChunksDir = chunks_dir

            session.add(chunkgroup)
            pydantic_chunkgroup = IndexedDocumentChunkGroupPydantic.from_orm(chunkgroup)
            return pydantic_chunkgroup

        except Exception as e:
            logger.error(f"RAGDBRepository.createChunkGroup: Failed to create chunkgroup document {doc_id}. Error={str(e)}")
            raise

    '''
    For each file in the chunks_dir, create the corresponding chunk in the database and add it to the chunk group.
    Returns an array of chunk info.
    '''
    def create_chunks(self, chunk_group_id, chunks_dir, session):
        result = []
        try:
            chunk_group = session.query(IndexedDocumentChunkGroup).filter_by(Id=chunk_group_id).first()

            chunk_ids = os.listdir(chunks_dir)
            for chunk_id in tqdm(chunk_ids):
                chunk = IndexedDocumentChunk()
                chunk.Id = str(uuid.uuid4())
                chunk.ChunkGroupId = chunk_group.Id

                # Load content
                chunk.Content = None
                with open(os.path.join(chunks_dir, chunk_id), 'rb') as f:
                    chunk.Content = f.read().decode('utf-8')
                    chunk.ByteSize = len(chunk.Content)

                # Create chunk hash and check for mismatch
                chunk.ChunkHash = file_utils.create_chunk_id_base64(chunk.Content)
                if (chunk.ChunkHash != chunk_id):
                    raise ValueError(f"RAGDBRepository.create_chunks: Chunk hash mismatch: {chunk.ChunkHash} != {chunk_id}")

                # Check for chunk hash duplicates in DB
                found = session.query(IndexedDocumentChunk).filter_by(ChunkHash=chunk_id).first()

                chunk.IsDuplicate= (found is not None)
                chunk.IsIndexed = False 
                chunk_group.Chunks.append(chunk)
                session.add(chunk)

                result.append(ChunkInfoPydantic(
                    Id=chunk.Id, 
                    ChunkHash=chunk.ChunkHash, 
                    IsDuplicate=chunk.IsDuplicate, 
                    IsIndexed=chunk.IsIndexed))
            session.commit()
            return result
        except Exception as e:
            logger.error(f"RAGDBRepository.create_chunks: Error splitting chunks for group {chunk_group_id}. Error={str(e)}")
            raise

# Collections -------------------------------------------------------------------------------------------------------------------------------------------

    def purge(self):
        metadata = MetaData()
        metadata.reflect(bind=self.engine)
        metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(self.engine)

    '''
    Delete all the documents (and its chunks) with the given collection name.
    '''
    def delete_collection(self, collection_name):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            documents = session.query(IndexedDocument).filter_by(CollectionName=collection_name).all()
            for document in documents:
                self.delete_document(collection_name=collection_name, doc_id=document.Id)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"RAGDBRepository: Error deleting collection {collection_name}. Error={str(e)}")
            raise
        finally:
            session.close()

    def collection_chunk_count(self,collection_name):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            chunks = session.query(IndexedDocumentChunk).join(IndexedDocumentChunkGroup).join(IndexedDocument).filter(IndexedDocument.CollectionName==collection_name).all()
            return len(chunks)
        except Exception as e:
            session.rollback()
            logger.error(f"RAGDBRepository: Error getting chunk count for collection {collection_name}. Error={str(e)}")
            raise
        finally:
            session.close()


# Documents -------------------------------------------------------------------------------------------------------------------------------------------

    def update_document(self, collection_name, document_id, document):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            existing_doc = session.query(IndexedDocument).filter(
                IndexedDocument.Id==document_id, 
                IndexedDocument.CollectionName==collection_name
                ).first()

            if existing_doc is not None:
                # Update all fields as necessary
                existing_doc.FileName = document.FileName
                existing_doc.Source = document.Source
                existing_doc.Abstract = document.Abstract
                existing_doc.Authors = document.Authors
                existing_doc.Title = document.Title
                existing_doc.Publisher = document.Publisher

                if document.PublishedDate and isinstance(document.PublishedDate,str):
                    try:
                        existing_doc.PublishedDate = datetime.strptime(document.PublishedDate, '%Y-%b-%d')
                    except:
                        existing_doc.PublishedDate = None
                else:
                    existing_doc.PublishedDate = None

                existing_doc.Comments = document.Comments
                existing_doc.UpdatedAt = datetime.now()

                session.commit()
                return existing_doc
            else:
                raise ValueError("No document found with the provided Id.")
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def get_document(self, collection_name, doc_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            return session.query(IndexedDocument).options(
                selectinload(IndexedDocument.ChunkGroups).
                selectinload(IndexedDocumentChunkGroup.Chunks)
                ).filter(
                IndexedDocument.Id==doc_id, 
                IndexedDocument.CollectionName==collection_name
                ).first()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    # This will return only the document header + chunk groups excl file content and chunks.
    def get_document_header(self, collection_name, doc_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            summary = session.query(IndexedDocument).options(
                selectinload(IndexedDocument.ChunkGroups),
                defer(IndexedDocument.File)
                ).filter(
                IndexedDocument.Id==doc_id, 
                IndexedDocument.CollectionName==collection_name
                ).first()
            
            return IndexedDocumentHeaderPydantic.from_orm(summary)
            
        except:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_document(self, collection_name, doc_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            document = session.query(IndexedDocument).filter(
                IndexedDocument.Id==doc_id, 
                IndexedDocument.CollectionName==collection_name
                ).first()
            if document is None:
                raise ValueError("No document found with the provided Id.")
            for chunk_group in document.ChunkGroups:
                for chunk in chunk_group.Chunks:
                    session.delete(chunk)
                session.delete(chunk_group)
            session.delete(document)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


    def list_document_headers(self, collection_name=None):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            if collection_name is None:
                documents=session.query(IndexedDocument).all()
            else:
                documents=session.query(IndexedDocument).filter_by(CollectionName=collection_name).all()
            result = []
            for document in documents:
                result.append(IndexedDocumentHeaderPydantic.from_orm(document))
            return result
        except:
            session.rollback()
            raise
        finally:
            session.close()

# ChunkGroups -------------------------------------------------------------------------------------------------------------------------------------------

    def get_chunkgroup(self, chunk_group_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            return session.query(IndexedDocumentChunkGroup).filter_by(Id=chunk_group_id).first()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    # The purpose for this function is to check how many groups does this chunk belongs to. Used when deleting chunks.
    def list_chunkgroups_by_chunkhash(self, chunk_hash):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            return session.query(IndexedDocumentChunkGroup).join(IndexedDocumentChunk).filter(IndexedDocumentChunk.ChunkHash==chunk_hash).all()
        except:
            session.rollback()
            raise
        finally:
            session.close()


    def delete_chunkgroup(self, chunk_group_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            chunkgroup = session.query(IndexedDocumentChunkGroup).filter_by(Id=chunk_group_id).first()
            if chunkgroup is None:
                raise ValueError("No chunk group found with the provided Id.")
            for chunk in chunkgroup.Chunks:
                session.delete(chunk)
            session.delete(chunkgroup)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()


# Chunks -------------------------------------------------------------------------------------------------------------------------------------------

    def document_chunk_count(self,collection_name, document_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            chunks = session.query(IndexedDocumentChunk).join(IndexedDocumentChunkGroup).join(IndexedDocument).filter(IndexedDocument.Id==document_id and IndexedDocument.CollectionName==collection_name).all()
            return len(chunks)
        except Exception as e:
            session.rollback()
            logger.error(f"RAGDBRepository: Error getting chunk count for collection {document_id}. Error={str(e)}")
            raise
        finally:
            session.close()

    def get_chunk(self, chunk_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            return session.query(IndexedDocumentChunk).filter_by(Id=chunk_id).first()
        except Exception as e:
            session.rollback()
            logger.error(f"RAGDBRepository: Error getting chunk {chunk_id}. Error={str(e)}")
            raise
        finally:
            session.close()

    def delete_chunk(self, chunk_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            chunk = session.query(IndexedDocumentChunk).filter_by(Id=chunk_id).first()
            session.delete(chunk)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"RAGDBRepository: Error getting chunk {chunk_id}. Error={str(e)}")
            raise
        finally:
            session.close()

    def list_chunks(self):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            return session.query(IndexedDocumentChunk).all()
        except Exception as e:
            session.rollback()
            logger.error(f"RAGDBRepository: Error listing chunks. Error={str(e)}")
            raise
        finally:
            session.close()


    def list_chunks_by_chunkgroup_id(self, chunkgroup_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            return session.query(IndexedDocumentChunk).filter_by(ChunkGroupId=chunkgroup_id).all()
        except Exception as e:
            session.rollback()
            logger.error(f"RAGDBRepository: Error listing chunks for group {chunkgroup_id}. Error={str(e)}")
            raise
        finally:
            session.close()

    def list_chunks_by_document_id(self, collection_name, doc_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            doc = session.query(IndexedDocument).options(selectinload(IndexedDocument.ChunkGroups)).filter(
                IndexedDocument.Id==doc_id,
                IndexedDocument.CollectionName==collection_name
                ).first()
            if not doc:
                return []
            chunks = doc.ChunkGroups[0].Chunks
            return chunks
        except Exception as e:
            logger.error(f"RAGDBRepository: Error listing chunks for document {doc_id}. Error={str(e)}")
            session.rollback()
            raise
        finally:
            session.close()


    def delete_chunks_by_document_id(self, doc_id):
        Session = sessionmaker(bind=self.engine)
        session = Session()
        try:
            doc = session.query(IndexedDocument).options(selectinload(IndexedDocument.ChunkGroups)).filter_by(Id=doc_id).first()
            if not doc:
                return
            for chunk in doc.ChunkGroups[0].Chunks:
                session.delete(chunk)
            session.commit()
        except Exception as e:
            logger.error(f"RAGDBRepository: Error deleting chunks for document {doc_id}. Error={str(e)}")
            session.rollback()
            raise
        finally:
            session.close()

#-------------------------------------------------------------------------------------------------------------------------------------------

    def __init__(self, engine):
        self.engine = engine

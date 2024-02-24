import tempfile
import time
import os
import uuid
from gai.gen.rag.dalc.RAGVSRepository import RAGVSRepository
import torch
import gc
from tqdm import tqdm
from datetime import datetime
from chromadb.utils.embedding_functions import InstructorEmbeddingFunction
from chromadb.config import Settings
import chromadb
from gai.common.utils import get_gen_config, get_app_path
import threading
from gai.common import logging, file_utils
from gai.common.StatusUpdater import StatusUpdater
from gai.gen.rag.dalc.RAGDBRepository import RAGDBRepository
from gai.gen.rag.dalc.IndexedDocument import IndexedDocument
logger = logging.getLogger(__name__)
import json


class RAG:

    def __init__(self, status_updater=None, in_memory=True):

        # Generator config
        self.generator_name = "rag"
        self.config = get_gen_config()["gen"]["rag"]
        app_path = get_app_path()
        self.model_path = os.path.join(app_path, self.config["model_path"])
        if (os.environ.get("RAG_MODEL_PATH")):
            model_path = os.environ["RAG_MODEL_PATH"]
            self.model_path = os.path.join(app_path, model_path)
        self.n_results = self.config["chromadb"]["n_results"]
        self.device = self.config["device"]
        
        # vector store config
        self.vs_repo = RAGVSRepository.New(in_memory)
        
        # document store config
        self.db_repo = RAGDBRepository.New(in_memory)

        # StatusUpdater
        self.status_updater = status_updater

        # for thread safety, using Semaphore allows for easier upgrade to support multiple generators in the future
        self.semaphore = threading.Semaphore(1)

    # Load Instructor model
    def load(self):
        self.vs_repo._ef = InstructorEmbeddingFunction(self.model_path, device=self.device)

    def unload(self):
        try:
            del self.vs_repo._ef
        except:
            pass
        self.vs_repo._ef = None
        gc.collect()
        torch.cuda.empty_cache()

    def reset(self):
        logger.info("Deleting database...")
        try:
            self.vs_repo.reset()
        except Exception as e:
            if not "does not exist." in str(e):
                logger.warning(f"reset: {e}")
                raise e

#Collections-------------------------------------------------------------------------------------------------------------------------------------------

    def list_collections(self):
        return self.vs_repo.list_collections()

    def delete_collection(self, collection_name):
        logger.info(f"Deleting {collection_name}...")
        try:
            self.vs_repo.delete_collection(collection_name)
            self.db_repo.delete_collection(collection_name)
        except Exception as e:
            if "does not exist." in str(e):
                logger.warning(f"delete_collection: {e}")
                return
            raise
    

#Documents-------------------------------------------------------------------------------------------------------------------------------------------
    
    def list_document_headers(self,collection_name=None):
        return self.db_repo.list_document_headers(collection_name)

    def create_document_hash(self, file):
        return self.db_repo.create_document_hash(file)

    def get_document(self,collection_name, document_id):
        return self.db_repo.get_document(collection_name, document_id)

    def get_document_header(self,collection_name, document_id):
        return self.db_repo.get_document_header(collection_name, document_id)

    def update_document(self,collection_name, document_id, document):
        return self.db_repo.update_document(collection_name, document_id, document)

    def delete_document(self,collection_name, document_id):
        logger.info(f"Deleting document {document_id} from collection {collection_name}...")
        self.vs_repo.delete_document(collection_name, document_id)
        self.db_repo.delete_document(collection_name, document_id)
            
    def delete_chunkgroup(self,collection_name, chunkgroup_id):
        chunkgroup = self.db_repo.get_chunkgroup(chunkgroup_id)
        logger.info(f"Deleting chunkgroup {chunkgroup_id} from collection {collection_name} with chunksize {chunkgroup.ChunkSize} and chunk count {chunkgroup.ChunkCount}...")
        self.vs_repo.delete_chunkgroup(collection_name, chunkgroup_id)
        self.db_repo.delete_chunkgroup(chunkgroup_id)

    def get_doc_id(self, file_path):
        doc_id = self.db_repo.create_document_hash(self, file_path)
        doc = self.db_repo.get_document(doc_id)
        if doc:
            return doc_id
        return None


#chunks-------------------------------------------------------------------------------------------------------------------------------------------

    def list_chunks_by_document_id(self,collection_name,doc_id):
        final=[]
        db_chunks = self.db_repo.list_chunks_by_document_id(collection_name, doc_id)
        for db_chunk in db_chunks:
            vs_chunk = self.vs_repo.get_chunk(collection_name, db_chunk.Id)
            db_chunk.Content = None
            if vs_chunk:
                if 'documents' in vs_chunk and len(vs_chunk['documents']) > 0:
                    db_chunk.Content = vs_chunk['documents'][0]
            final.append(db_chunk)
        return final

    def get_chunk(self,collection_name, chunk_id):
        return self.vs_repo.get_chunk(collection_name, chunk_id)
    
    def delete_chunk(self, collection_name, chunk_id):
        self.vs_repo.delete_chunk(collection_name, chunk_id)
        self.db_repo.delete_chunk(chunk_id)

#Indexing-------------------------------------------------------------------------------------------------------------------------------------------

    # Split text in temp dir and index each chunk into vector store locally.
    # Public. Used by rag_api and Gaigen.
    async def index_async(self, 
        collection_name, 
        file_path, 
        file_type=None,
        title='', 
        source= '', 
        abstract='',
        authors='',
        publisher ='',
        published_date='', 
        comments='',
        keywords='',
        chunk_size=None, 
        chunk_overlap=None, 
        status_updater=None):
        if status_updater:
            logger.info(
                f"RAG.index_async: status_updater detected.")
            
        if file_type is None:
            _,file_type = os.path.splitext(file_path)

        ids = []
        if chunk_size is None:
            chunk_size = self.config["chunks"]["size"]
        if chunk_overlap is None:
            chunk_overlap = self.config["chunks"]["overlap"]

        # Create document ID first and check for duplicates
        try:
            doc_id = self.db_repo.create_document_hash(file_path=file_path)
            logger.info(f"rag.index_async: document_id={doc_id}")
        except Exception as error:
            logger.error(
                f"RAG.index_async: Failed to create document hash. error={error}. Not created in database yet.")
            raise error
        
        try:
            # Create the document header to store the original
            doc=self.db_repo.create_document_header(
                id = doc_id,
                collection_name=collection_name, 
                file_path=file_path, 
                file_type=file_type,
                title=title, 
                source=source, 
                abstract=abstract,
                authors=authors,
                publisher = publisher,
                published_date=published_date, 
                comments=comments,
                keywords=keywords)
            logger.info(f"rag.index_async: document_header created. id={doc_id}")
            # Create the first chunk group based on the default splitting algorithm
            chunkgroup = self.db_repo.create_chunkgroup(
                doc_id=doc.Id, 
                chunk_size=chunk_size, 
                chunk_overlap=chunk_overlap, 
                splitter=file_utils.split_file)
            
            logger.info(f"rag.index_async: chunkgroup created. chunkgroup_id={chunkgroup.Id}")

            # Create the chunks in the database
            chunks = self.db_repo.create_chunks(
                chunkgroup.Id,
                chunkgroup.ChunksDir
            )

            logger.info(f"rag.index_async: chunks header created. count={len(chunks)}")

            # Index each chunk into the vector store
            logger.info(f"RAG.index_async: Begin indexing...")
            for i, chunk in tqdm(enumerate(chunks)):
                chunk = self.db_repo.get_chunk(chunk.Id)
                self.vs_repo.index_chunk(
                    collection_name=collection_name, 
                    content=chunk.Content, 
                    chunk_id=chunk.Id, 
                    document_id=doc_id,
                    chunkgroup_id=chunkgroup.Id,
                    source=doc.Source if doc.Source else "",
                    abstract=doc.Abstract if doc.Abstract else "",
                    title=doc.Title if doc.Title else "",
                    published_date=doc.PublishedDate.strftime('%Y-%b-%d') if doc.PublishedDate else "",
                    keywords=doc.Keywords if doc.Keywords else ""
                )
                ids.append(chunk.Id)
                logger.debug(
                    f"RAG.index_async: Indexed {i+1}/{len(chunks)} chunk {chunk.Id} into collection {collection_name}")

                # Callback for progress update
                if status_updater:
                    logger.debug(f"RAG.index_async: Send progress {i+1} to updater")
                    await status_updater.update_progress(i+1, len(chunks))

            # Send stop token
            if status_updater:
                logger.debug("RAG.index_async: Sending stop token")
                await status_updater.update_stop()

            logger.info(f"RAG.index_async: indexing...done")
            return doc_id
        except Exception as error:
            # Once encounter an exception, revert to a clean state.
            logger.info("Error encountered. Try deleting all created chunks and chunkgroup.")
            try:
                self.vs_repo.delete_document(collection_name, doc_id)
                self.db_repo.delete_document(collection_name, doc_id)
            except Exception as e:
                logger.error(f"RAG.index_async: Failed to delete document. error={e}")
            if "Document already exists" in str(error):
                logger.error(
                    f"File already exists in the database. doc_id={doc_id}")
                raise error

            logger.error(
                f"RAG.index_async: Failed to create document header. error={error}")
            raise error

    # RETRIEVAL
    def retrieve(self, collection_name, query_texts, n_results=None):
        logger.info(f"Retrieving by query {query_texts}...")

        if n_results is None:
            n_results = self.n_results
        result = self.vs_repo.retrieve(collection_name, query_texts, n_results)

        # Not found
        if 'ids' not in result or result['ids'] is None or len(result['ids']) == 0 or len(result['ids'][0]) == 0:
            return None

        ids = result['ids']
        if len(ids) > 0:
            logger.debug(f'result={result.to_json()}')

        import pandas as pd
        df = pd.DataFrame({
            'documents': result['documents'][0],
            'metadatas': result['metadatas'][0],
            'distances': result['distances'][0],
            'ids': result['ids'][0]
        })

        # drop duplicates
        return df.drop_duplicates(subset=['ids']).sort_values('distances', ascending=True)


        
import unittest
import os, sys
from gai.common import file_utils
from gai.gen.rag.dalc.IndexedDocumentChunk import IndexedDocumentChunk
from gai.gen.rag.dalc.IndexedDocumentChunkGroup import IndexedDocumentChunkGroup
from gai.gen.rag.models.IndexedDocumentChunkGroupPydantic import IndexedDocumentChunkGroupPydantic
sys.path.insert(0,os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from gai.gen.rag.dalc.IndexedDocument import IndexedDocument
from sqlalchemy.orm import sessionmaker

from datetime import datetime
from gai.gen.rag.dalc.RAGDBRepository import RAGDBRepository as Repository
from gai.gen.rag.RAG import RAG
from gai.common.logging import getLogger
logger = getLogger(__name__)

class UT0010_RAGDBRepository_test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.repo = Repository.New(in_memory=True)

#-------------------------------------------------------------------------------------------------------------------------------------------
        
    def test_ut0011_convert_and_load_pdffile(self):
        file_path = os.path.join(os.path.dirname(__file__), "attention-is-all-you-need.pdf")
        content = self.repo.load_and_convert(file_path=file_path, file_type=file_path.split('.')[-1])
        self.assertTrue(content.startswith("3 2 0 2 g u A 2 ] L C . s c [ 7 v 2 6 7 3 0 . 6 0 7 1"))

    def test_ut0012_convert_and_load_textfile(self):
        file_path = os.path.join(os.path.dirname(__file__), "pm_long_speech_2023.txt")
        content = self.repo.load_and_convert(file_path=file_path, file_type=file_path.split('.')[-1])
        self.assertTrue(content.startswith('PM Lee Hsien Loong delivered'))

#-------------------------------------------------------------------------------------------------------------------------------------------
    def test_ut0013_create_document_id(self):
        # Arrange
        file_path = os.path.join(os.path.dirname(__file__), "attention-is-all-you-need.pdf")
        doc_id = self.repo.create_document_hash(file_path)
        self.assertEqual("f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d",doc_id)

    def test_ut0014_create_document_header(self):

        # Arrange
        file_path = os.path.join(os.path.dirname(__file__), "attention-is-all-you-need.pdf")

        # Act
        doc=self.repo.create_document_header(
            id="f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d",
            collection_name='demo', 
            file_path=file_path, 
            file_type='pdf',
            title='Attention is All You Need', 
            source='https://arxiv.org/abs/1706.03762', 
            abstract="""The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature. We show that the Transformer generalizes well to other tasks by applying it successfully to English constituency parsing both with large and limited training data""",
            authors='Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin',
            publisher = 'arXiv',
            publishedDate='2017-June-12', 
            comments='This is a test document')


        # Assert
        retrieved_doc = self.repo.get_document(doc.Id)

        # Ensure the document was retrieved
        self.assertIsNotNone(retrieved_doc)

        # Check each field for correctness
        self.assertEqual(retrieved_doc.CollectionName, 'demo')
        self.assertEqual(os.path.basename(retrieved_doc.FileName), os.path.basename(file_path))
        self.assertEqual(retrieved_doc.ByteSize, os.path.getsize(file_path))
        self.assertEqual(retrieved_doc.FileType, 'pdf')
        self.assertEqual(retrieved_doc.Title, 'Attention is All You Need')
        self.assertEqual(retrieved_doc.Source, 'https://arxiv.org/abs/1706.03762')
        self.assertEqual(retrieved_doc.Abstract, """The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature. We show that the Transformer generalizes well to other tasks by applying it successfully to English constituency parsing both with large and limited training data""")
        self.assertEqual(retrieved_doc.Authors, 'Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin')
        self.assertEqual(retrieved_doc.Publisher, 'arXiv')
        self.assertEqual(retrieved_doc.PublishedDate, datetime.strptime('2017-June-12','%Y-%B-%d').date())
        self.assertEqual(retrieved_doc.Comments, 'This is a test document')

        # Additional checks for fields with default values or calculated fields
        self.assertEqual(retrieved_doc.IsActive, True)
        self.assertIsNotNone(retrieved_doc.CreatedAt)
        self.assertIsNotNone(retrieved_doc.UpdatedAt)

        # compare the file content
        with open(file_path, 'rb') as f:
            expected_file_content = f.read()
        self.assertEqual(retrieved_doc.File, expected_file_content)


    def test_ut0015_should_not_create_duplicate(self):
        # Arrange
        file_path = os.path.join(os.path.dirname(__file__), "attention-is-all-you-need.pdf")
        # Act
        try:
            self.repo.create_document_header(
                id="f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d",
                collection_name='demo', 
                file_path=file_path, 
                file_type='pdf',
                title='Attention is All You Need', 
                source='https://arxiv.org/abs/1706.03762', 
                abstract="""The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train. Our model achieves 28.4 BLEU on the WMT 2014 English-to-German translation task, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs, a small fraction of the training costs of the best models from the literature. We show that the Transformer generalizes well to other tasks by applying it successfully to English constituency parsing both with large and limited training data""",
                authors='Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin',
                publisher = 'arXiv',
                publishedDate='2017-June-12', 
                comments='This is a test document')
        except Exception as e:
            self.assertTrue(str(e).startswith("Document already exists in the database"))

#-------------------------------------------------------------------------------------------------------------------------------------------

    def test_ut0016_create_chunk_group(self):

        # Act
        chunkgroup = self.repo.create_chunkgroup(
            doc_id='f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d', 
            chunk_size=1000, 
            chunk_overlap=100, 
            splitter=file_utils.split_file)

        # Assert
        engine = self.repo.engine
        Session = sessionmaker(bind=engine)
        session = Session()

        retrieved_doc = session.query(IndexedDocument).filter_by(Id='f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d').first()
        retrieved_group = session.query(IndexedDocumentChunkGroup).filter_by(Id=chunkgroup.Id).first()

        # Assert: Can get group from doc
        self.assertEqual(len(retrieved_doc.ChunkGroups),1)

        # Assert: Can get group from DB
        self.assertIsNotNone(retrieved_group)

        # Assert: Chunk group has correct number of chunks
        file_chunks = os.listdir(retrieved_group.ChunksDir)
        self.assertEqual(retrieved_group.ChunkCount, len(file_chunks))

#-------------------------------------------------------------------------------------------------------------------------------------------

    def test_ut0017_create_chunks(self):

        #Act
        group = self.repo.get_document('f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d').ChunkGroups[0]
        chunks = self.repo.create_chunks(group.Id,group.ChunksDir)

        # Assert

        # List all chunks
        retrieved_chunks = self.repo.list_chunks()
        self.assertEqual(len(chunks), len(retrieved_chunks))
        for i in range(len(retrieved_chunks)):
            self.assertEqual(retrieved_chunks[i].Id,chunks[i].Id)

        # List only chunks by id
        retrieved_chunks = self.repo.list_chunks_by_document_id('f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d')
        self.assertEqual(len(chunks), len(retrieved_chunks))
        for i in range(len(retrieved_chunks)):
            self.assertEqual(retrieved_chunks[i].Id,chunks[i].Id)
        
#-------------------------------------------------------------------------------------------------------------------------------------------

    def test_ut0018_delete_document(self):

        # Act
        self.repo.delete_document('f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d')

        # Assert
        engine = self.repo.engine
        Session = sessionmaker(bind=engine)
        session = Session()
        retrieved_doc = session.query(IndexedDocument).filter_by(Id='f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d').first()
        self.assertIsNone(retrieved_doc)

        retrieved_group = session.query(IndexedDocumentChunkGroup).filter_by(DocumentId='f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d').first()
        self.assertIsNone(retrieved_group)

        retrieved_chunks = session.query(IndexedDocumentChunk).all()
        self.assertEqual(len(retrieved_chunks), 0)

#-------------------------------------------------------------------------------------------------------------------------------------------

    def test_ut0019_delete_collection(self):

        # Arrange
        doc_id=self.repo.create_document_header(
            id='f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d',
            collection_name='demo', 
            file_path=os.path.join(os.path.dirname(__file__), "attention-is-all-you-need.pdf"),
            file_type='pdf'
        )

        # Act
        self.repo.delete_collection('demo')

        # Assert
        engine = self.repo.engine
        Session = sessionmaker(bind=engine)
        session = Session()
        retrieved_doc = session.query(IndexedDocument).filter_by(Id='f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d').first()
        self.assertIsNone(retrieved_doc)

#-------------------------------------------------------------------------------------------------------------------------------------------
    
    def test_ut0020_delete_chunks_by_document_id(self):
            
            # Arrange
            doc=self.repo.create_document_header(
                id='f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d',
                collection_name='demo', 
                file_path=os.path.join(os.path.dirname(__file__), "attention-is-all-you-need.pdf"),
                file_type='pdf'
            )
            group = self.repo.create_chunkgroup(
                doc_id=doc.Id, 
                chunk_size=1000, 
                chunk_overlap=100, 
                splitter=file_utils.split_file)
            self.repo.create_chunks(group.Id,group.ChunksDir)
    
            # Act
            self.repo.delete_chunks_by_document_id('f9273d797cd489295a155dea10368a6a6df70686a692fbf8b5e6bc60fb23a72d')
    
            # Assert
            engine = self.repo.engine
            Session = sessionmaker(bind=engine)
            session = Session()
            retrieved_chunks = session.query(IndexedDocumentChunk).all()
            self.assertEqual(len(retrieved_chunks), 0)


#-------------------------------------------------------------------------------------------------------------------------------------------
    
    def test_ut0021_list_documents(self):
            
        # Arrange
        self.repo.create_document_header(
            id='80c7064c-b446-45cc-8f0e-8cc781eb3ecb',
            collection_name='demo1', 
            file_path=os.path.join(os.path.dirname(__file__), "attention-is-all-you-need.pdf"),
            file_type='pdf'
        )
        self.repo.create_document_header(
            id='d8a4994e-8df1-41bd-acf0-0ea52cb4c10e',
            collection_name='demo1', 
            file_path=os.path.join(os.path.dirname(__file__), "attention-is-all-you-need.pdf"),
            file_type='pdf'
        )

        # Act
        docs = self.repo.list_documents()

        # Assert
        self.assertEqual(len(docs), 3)

        # Act
        docs = self.repo.list_documents('demo1')

        # Assert
        self.assertEqual(len(docs), 2)




if __name__ == '__main__':
    logger.setLevel('INFO')
    unittest.main(exit=False)

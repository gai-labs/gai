import os, sys

from gai.common.errors import DuplicatedDocumentException, ApiException
sys.path.insert(0,os.path.join(os.path.dirname(__file__), "..", "..", "..",".."))
from gai.lib.RAGClientSync import RAGClientSync
import unittest
from gai.common.logging import getLogger
logger = getLogger(__name__)


class UT0110_RAGClient_test(unittest.TestCase):

#-------------------------------------------------------------------------------------------------------------------------------------------

    def test_ut0111_purge(self):
        client = RAGClientSync("./rag-test.yml")
        client.purge_all()

    def test_ut0112_index_document(self):
        client = RAGClientSync("./rag-test.yml")
        result = client.index_file(
            file_path="./attention-is-all-you-need.pdf",
            collection_name="demo",
            title="Attention is all you need",
            authors= "Vaswani et al."
        )
        self.assertEqual(result,"-Sc9eXzUiSlaFV3qEDaKam33Boamkvv4tea8YPsjpy0")

    def test_ut0113_should_not_allow_duplicate(self):
        client = RAGClientSync("./rag-test.yml")
        try:
            client.index_file(
                file_path="./attention-is-all-you-need.pdf",
                collection_name="demo",
                title="Attention is all you need",
                authors= "Vaswani et al."
            )
            raise Exception("Failed to raise exception")
        except ApiException as e:
            print(type(e))
            self.assertEqual(e.code,"duplicate_document")

    def test_ut0114_delete_if_available(self):
        rag = RAGClientSync("./rag-test.yml")
        result = rag.delete_document(
            collection_name='demo',
            doc_id="-Sc9eXzUiSlaFV3qEDaKam33Boamkvv4tea8YPsjpy0"
        )
        print(result)


if __name__ == "__main__":
    unittest.main()

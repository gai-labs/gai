import os, sys
#sys.path.insert(0,os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from gai.lib.RAGClientSync import RAGClientSync
import unittest
from gai.common.logging import getLogger
logger = getLogger(__name__)


class UT0110_RAGClient_test(unittest.TestCase):

#-------------------------------------------------------------------------------------------------------------------------------------------
        
    # def test_ut0111_index_document(self):
    #     rag = RAGClientSync()
    #     result = rag.index_file(
    #         file_path="./attention-is-all-you-need.pdf",
    #         collection_name="demo",
    #         title="Attention is all you need",
    #         authors= "Vaswani et al."
    #     )
    #     print(result)

    def test_ut0111_delete_if_available(self):
        rag = RAGClientSync("gai/gai-lib/tests/clients/ut0110_rag/gai.yml")
        result = rag.delete_document(
            doc_id="-Sc9eXzUiSlaFV3qEDaKam33Boamkvv4tea8YPsjpy0"
        )
        print(result)

if __name__ == '__main__':
    logger.setLevel('INFO')
    unittest.main(exit=False)

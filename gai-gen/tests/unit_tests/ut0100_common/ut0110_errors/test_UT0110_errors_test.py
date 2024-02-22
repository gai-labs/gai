import unittest
from fastapi import HTTPException
from gai.common.errors import ApiException
import requests  # replace with the correct import path

class UT0110ErrorsTest(unittest.TestCase):

    def test_UT0111_ApiException(self):
        response = requests.get('http://localhost:12031/ApiException')
        print()
        print('status_code:',response.status_code)
        print('url:',response.url)
        print('json:',response.json() )
        print()

    def test_UT0112_InternalException(self):
        response = requests.get('http://localhost:12031/InternalException')
        print()
        print('status_code:',response.status_code)
        print('url:',response.url)
        print('json:',response.json() )
        print()

    def test_UT0113_JSONResponse(self):
        response = requests.get('http://localhost:12031/JSONResponse')
        print()
        print('status_code:',response.status_code)
        print('url:',response.url)
        print('json:',response.json() )
        print()

    def test_UT0114_MessageNotFoundException(self):
        response = requests.get('http://localhost:12031/MessageNotFoundException/abcd')
        print()
        print('status_code:',response.status_code)
        print('url:',response.url)
        print('json:',response.json() )
        print()

    def test_UT0115_UserNotFoundException(self):
        response = requests.get('http://localhost:12031/UserNotFoundException/1234')
        print()
        print('status_code:',response.status_code)
        print('url:',response.url)
        print('json:',response.json() )
        print()

    def test_UT0116_GeneratorMismatchException(self):
        response = requests.get('http://localhost:12031/GeneratorMismatchException')
        print()
        print('status_code:',response.status_code)
        print('url:',response.url)
        print('json:',response.json() )
        print()

    def test_UT0117_ContextLengthExceededException(self):
        response = requests.get('http://localhost:12031/ContextLengthExceededException')
        print()
        print('status_code:',response.status_code)
        print('url:',response.url)
        print('json:',response.json() )
        print()

if __name__ == '__main__':
    unittest.main()

import unittest
from fastapi import HTTPException
from gai.common.errors import ApiException  # replace with the correct import path

class TestApiException(unittest.TestCase):
    def setUp(self):
        self.exception = ApiException(status_code=404, code='not_found', message='Not Found', url='/test/url')

    def test_status_code(self):
        self.assertEqual(self.exception.status_code, 404)

    def test_detail(self):
        expected_detail = {
            "code": 'not_found',
            "message": 'Not Found',
            "url": '/test/url'
        }
        self.assertDictEqual(self.exception.detail, expected_detail)

    def test_raise_and_catch(self):
        try:
            raise ApiException(status_code=500, code='server_error', message='Server Error', url='/test/error')
        except ApiException as e:
            self.assertEqual(e.status_code, 500)
            self.assertDictEqual(e.detail, {
                "code": 'server_error',
                "message": 'Server Error',
                "url": '/test/error'
            })

    def test_raise_HTTPException(self):
        try:
            raise HTTPException(409, detail={
                "code": "conflict",
                "message": "Conflict",
                "url": "/test/conflict"
            })
        except HTTPException as e:
            self.assertEqual(e.status_code, 409)
            self.assertDictEqual(e.detail, {
                "code": "conflict",
                "message": "Conflict",
                "url": "/test/conflict"
            })

if __name__ == '__main__':
    unittest.main()

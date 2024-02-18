class HttpException(Exception):
    def __init__(self, status_code, code, message, url):
        self.status_code = status_code
        self.code = code
        self.url = url
        super().__init__(message)
    pass

class NormalException(Exception):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)
    pass
class HttpException(Exception):
    def __init__(self, status_code, code, message, url):
        self.message = message
        self.status_code = status_code
        self.code = code
        self.url = url
        super().__init__(self.message)
    pass
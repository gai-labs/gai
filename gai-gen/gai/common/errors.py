from fastapi import HTTPException

class ApiException(HTTPException):
    def __init__(self, status_code, code, message):
        super().__init__(status_code=status_code, detail = {
            "code": code,
            "message": message
        })

class DuplicatedDocumentException(HTTPException):
    def __init__(self):
        message = "Document already exists in the database."
        super().__init__(status_code=409, detail = {
            "code": "duplicate_document",
            "message": message
        })


class MessageNotFoundException(HTTPException):
    def __init__(self,message_id=None):
        message = "Message not found"
        if (message_id):
            message = f"Message {message_id} not found"
        super().__init__(status_code=404, detail = {
            "code": "message_not_found",
            "message": message
        })

class CollectionNotFoundException(HTTPException):
    def __init__(self,collection_name=None):
        message = "Collection not found"
        if (collection_name):
            message = f"Collection {collection_name} not found"
        super().__init__(status_code=404, detail = {
            "code": "collection_not_found",
            "message": message
        })

class DocumentNotFoundException(HTTPException):
    def __init__(self,document_id=None):
        message = "Document not found"
        if (document_id):
            message = f"Document {document_id} not found"
        super().__init__(status_code=404, detail = {
            "code": "document_not_found",
            "message": message
        })

class UserNotFoundException(HTTPException):
    def __init__(self,user_id=None):
        message = "User not found"
        if (user_id):
            message = f"User {user_id} not found"
        super().__init__(status_code=404, detail = {
            "code": "user_not_found",
            "message": message
        })

class ContextLengthExceededException(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail={
            "code": "context_length_exceeded",
            "message": "The context length exceeded the maximum allowed length."
        })

class GeneratorMismatchException(HTTPException):
    def __init__(self):
        super().__init__(status_code=409, detail={
            "code": "generator_mismatch",
            "message": "The model does not correspond to this service."
        })


class InternalException(HTTPException):
    def __init__(self, error_id):
        detail = {
            "code": "unknown_error",
            "message": "An unexpected error occurred. Please try again later.",
            "id": error_id,
        }
        super().__init__(status_code=500, detail=detail)



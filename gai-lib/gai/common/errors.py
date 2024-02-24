from fastapi import HTTPException

class ApiException(HTTPException):
    def __init__(self, status_code, code, message, url=None, *args, **kwargs):
        super().__init__(status_code=status_code, detail = {
            "code": code,
            "message": message,
            "url": url
        })

class InternalException(HTTPException):
    def __init__(self, error_id):
        detail = {
            "code": "unknown_error",
            "message": "An unexpected error occurred. Please try again later.",
            "id": error_id,
        }
        super().__init__(status_code=500, detail=detail)

class ContextLengthExceededException(HTTPException):
    def __init__(self):
        detail={
            "code": "context_length_exceeded",
            "message": "The context length exceeded the maximum allowed length."
        }
        super().__init__(status_code=400, detail=detail)

class GeneratorMismatchException(HTTPException):
    def __init__(self):
        detail={
            "code": "generator_mismatch",
            "message": "The model does not correspond to this service."
        }
        super().__init__(status_code=400, detail=detail)

class UserNotFoundException(HTTPException):
    def __init__(self,user_id=None):
        detail={
            "code": "user_not_found",
            "message": "User not found"
        }
        if user_id:
            detail["message"] = f"User {user_id} not found"
        super().__init__(status_code=404, detail=detail)

class MessageNotFoundException(HTTPException):
    def __init__(self,message_id=None):
        detail={
            "code": "message_not_found",
            "message": "Message not found"
        }
        if message_id:
            detail["message"] = f"Message {message_id} not found"
        super().__init__(status_code=404, detail=detail)

class CollectionsNotFoundException(HTTPException):
    def __init__(self,collection_name=None):
        detail={
            "code": "collection_not_found",
            "message": "Collection not found"
        }
        if collection_name:
            detail["message"] = f"Collection {collection_name} not found"
        super().__init__(status_code=404, detail=detail)


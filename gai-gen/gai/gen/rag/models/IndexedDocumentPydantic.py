from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class IndexedDocumentPydantic(BaseModel):
    Id: str = Field(...)
    CollectionName: str
    ByteSize: int
    FileName: Optional[str] = None
    FileType: Optional[str] = None
    File: Optional[bytes] = None  # Note: BLOB type in SQLAlchemy maps to bytes in Python
    Source: Optional[str] = None
    Abstract: Optional[str] = None
    Authors: Optional[str] = None
    Title: Optional[str] = None
    Publisher: Optional[str] = None
    PublishedDate: Optional[datetime] = None
    Comments: Optional[str] = None
    Keywords: Optional[str] = None
    IsActive: bool = True
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True
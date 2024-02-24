from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class IndexedDocumentHeaderPydantic(BaseModel):
    Id: str = Field(...)
    CollectionName: str
    ByteSize: int
    FileName: Optional[str] = None
    FileType: Optional[str] = None
    Source: Optional[str] = None
    Abstract: Optional[str] = None
    Authors: Optional[str] = None
    Title: Optional[str] = None
    Publisher: Optional[str] = None
    PublishedDate: Optional[datetime] = None
    Comments: Optional[str] = None
    Keywords: Optional[str] = None
    CreatedAt: datetime
    UpdatedAt: datetime

    class Config:
        from_attributes = True
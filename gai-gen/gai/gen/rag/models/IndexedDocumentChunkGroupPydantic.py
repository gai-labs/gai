from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID, uuid4

class IndexedDocumentChunkGroupPydantic(BaseModel):
    Id: str = Field(default_factory=uuid4)
    DocumentId: str  # Assuming DocumentId is also a UUID; adjust if it's not
    SplitAlgo: Optional[str] = None
    ChunkCount: int
    ChunkSize: int
    Overlap: int
    IsActive: bool = True
    ChunksDir: Optional[str] = None

    # If you have defined Pydantic models for IndexedDocument and IndexedDocumentChunk, you can include them like so:
    # Document: Optional[IndexedDocumentPydantic] = None
    # Chunks: List[IndexedDocumentChunkPydantic] = []

    class Config:
        from_attributes = True

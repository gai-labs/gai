from sqlalchemy import Column, Text, VARCHAR, DateTime, Boolean, BLOB, JSON, INTEGER, Date,BIGINT
from sqlalchemy.orm import relationship
from gai.gen.rag.dalc.Base import Base
from gai.gen.rag.dalc.IndexedDocumentChunk import IndexedDocumentChunk

class IndexedDocument(Base):
    __tablename__ = 'IndexedDocuments'

    Id = Column(VARCHAR(44), primary_key=True)
    CollectionName = Column(VARCHAR(200), nullable=False)
    ByteSize = Column(BIGINT, nullable=False)
    FileName = Column(VARCHAR(200))
    FileType = Column(VARCHAR(10))
    File = Column(BLOB)
    Source = Column(VARCHAR(255))
    Abstract = Column(Text)
    Authors = Column(VARCHAR(255))
    Title = Column(VARCHAR(255))
    Publisher = Column(VARCHAR(255))
    PublishedDate = Column(Date)
    Comments = Column(Text)
    Keywords = Column(Text)
    IsActive = Column(Boolean, default=True)
    CreatedAt = Column(DateTime)
    UpdatedAt = Column(DateTime)

    ChunkGroups = relationship("IndexedDocumentChunkGroup", back_populates="Document")
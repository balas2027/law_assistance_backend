from app.repositories.base import CRUDBase
from app.models.document import Document
from app.schemas.document import DocumentCreate

class DocumentRepository(CRUDBase[Document, DocumentCreate, DocumentCreate]):
    pass

document_repository = DocumentRepository(Document)

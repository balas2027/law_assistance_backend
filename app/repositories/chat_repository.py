from app.repositories.base import CRUDBase
from app.models.chat import Chat
from app.schemas.chat import ChatCreate

class ChatRepository(CRUDBase[Chat, ChatCreate, ChatCreate]):
    pass

chat_repository = ChatRepository(Chat)

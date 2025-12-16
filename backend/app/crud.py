from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.models import ChatSession, ChatMessage
from app.schemas import SessionCreate, MessageCreate

# ====================== 会话操作函数 ======================

def create_session(db: Session, session_data: SessionCreate) -> ChatSession:
    """创建新的聊天会话"""
    db_session = ChatSession(
        title=session_data.title
    )
    
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    
    return db_session

def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
    """获取聊天会话"""
    return db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.is_active == True
    ).first()

def get_all_sessions(db: Session) -> List[ChatSession]:
    """获取所有聊天会话"""
    return db.query(ChatSession).filter(
        ChatSession.is_active == True
    ).order_by(ChatSession.updated_at.desc()).all()

def update_session(db: Session, session_id: str, update_data: Dict[str, Any]) -> Optional[ChatSession]:
    """更新会话信息"""
    session = get_session(db, session_id)
    if session:
        for key, value in update_data.items():
            if hasattr(session, key):
                setattr(session, key, value)
        session.updated_at = datetime.now()
        db.commit()
        db.refresh(session)
    return session

def delete_session(db: Session, session_id: str) -> bool:
    """删除聊天会话（软删除）"""
    session = get_session(db, session_id)
    if session:
        session.is_active = False
        session.updated_at = datetime.now()
        db.commit()
        return True
    return False

# ====================== 消息操作函数 ======================

def create_message(db: Session, message_data: MessageCreate) -> ChatMessage:
    """创建消息"""
    # 确保会话存在
    session = get_session(db, message_data.session_id)
    if not session:
        # 创建新会话
        session = create_session(db, SessionCreate(title="新对话"))
    
    db_message = ChatMessage(
        session_id=session.id,
        role=message_data.role,
        content=message_data.content,
        tool_calls=message_data.tool_calls,
        tool_results=message_data.tool_results
    )
    
    db.add(db_message)
    
    # 更新会话时间
    session.updated_at = datetime.now()
    db.commit()
    db.refresh(db_message)
    
    return db_message

def get_messages(db: Session, session_id: str, limit: int = 50) -> List[ChatMessage]:
    """获取会话消息"""
    return db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).limit(limit).all()

def get_message(db: Session, message_id: str) -> Optional[ChatMessage]:
    """获取特定消息"""
    return db.query(ChatMessage).filter(
        ChatMessage.id == message_id
    ).first()

def delete_messages(db: Session, session_id: str) -> int:
    """删除会话的所有消息"""
    result = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).delete()
    db.commit()
    return result

# ====================== 批量操作函数 ======================

def create_messages_batch(db: Session, messages_data: List[MessageCreate]) -> List[ChatMessage]:
    """批量创建消息"""
    messages = []
    for message_data in messages_data:
        message = create_message(db, message_data)
        messages.append(message)
    return messages

def get_recent_sessions(db: Session, limit: int = 10) -> List[ChatSession]:
    """获取最近活跃的会话"""
    return db.query(ChatSession).filter(
        ChatSession.is_active == True
    ).order_by(ChatSession.updated_at.desc()).limit(limit).all()

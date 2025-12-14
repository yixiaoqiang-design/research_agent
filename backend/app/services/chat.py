from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import SessionCreate, MessageCreate, ChatRequest
from app.services.agent import agent_service

import logging

logger = logging.getLogger(__name__)

class ChatService:
    """聊天服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, session_data: SessionCreate) -> ChatSession:
        """创建新的聊天会话"""
        session_id = str(uuid.uuid4())
        
        db_session = ChatSession(
            session_id=session_id,
            title=session_data.title
        )
        
        self.db.add(db_session)
        self.db.commit()
        self.db.refresh(db_session)
        
        return db_session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """获取聊天会话"""
        return self.db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_active == True
        ).first()
    
    def get_all_sessions(self) -> List[ChatSession]:
        """获取所有聊天会话"""
        return self.db.query(ChatSession).filter(
            ChatSession.is_active == True
        ).order_by(ChatSession.updated_at.desc()).all()
    
    def delete_session(self, session_id: str) -> bool:
        """删除聊天会话"""
        session = self.get_session(session_id)
        if session:
            session.is_active = False
            self.db.commit()
            return True
        return False
    
    def create_message(self, message_data: MessageCreate) -> ChatMessage:
        """创建消息"""
        # 确保会话存在
        session = self.get_session(message_data.session_id)
        if not session:
            # 创建新会话
            session = self.create_session(SessionCreate(title="新对话"))
        
        db_message = ChatMessage(
            session_id=message_data.session_id,
            role=message_data.role,
            content=message_data.content,
            tool_calls=message_data.tool_calls,
            tool_results=message_data.tool_results
        )
        
        self.db.add(db_message)
        
        # 更新会话时间
        session.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(db_message)
        
        return db_message
    
    def get_messages(self, session_id: str, limit: int = 50) -> List[ChatMessage]:
        """获取会话消息"""
        return self.db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.asc()).limit(limit).all()
    
    async def process_chat(self, chat_request: ChatRequest) -> Dict[str, Any]:
        """处理聊天请求"""
        session_id = chat_request.session_id
        
        # 如果没有session_id，创建新会话
        if not session_id:
            session = self.create_session(SessionCreate(title=chat_request.message[:50]))
            session_id = session.session_id
        
        # 获取历史消息
        history_messages = self.get_messages(session_id)
        history = []
        for msg in history_messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_results": msg.tool_results
            })
        
        # 保存用户消息
        user_message = self.create_message(MessageCreate(
            session_id=session_id,
            role="user",
            content=chat_request.message
        ))
        
        # 使用Agent处理消息
        agent_response = await agent_service.process_message(
            chat_request.message, 
            history
        )
        
        # 保存Assistant消息
        assistant_message = self.create_message(MessageCreate(
            session_id=session_id,
            role="assistant",
            content=agent_response["content"],
            tool_calls=agent_response["tool_calls"],
            tool_results=agent_response["tool_results"]
        ))
        
        return {
            "session_id": session_id,
            "message": assistant_message,
            "is_complete": True
        }
    
    async def process_stream_chat(self, chat_request: ChatRequest):
        """流式处理聊天请求"""
        logger.info("Processing stream chat request")
        session_id = chat_request.session_id
        
        # 如果没有session_id，创建新会话
        if not session_id:
            session = self.create_session(SessionCreate(title=chat_request.message[:50]))
            session_id = session.session_id
        
        # 保存用户消息
        user_message = self.create_message(MessageCreate(
            session_id=session_id,
            role="user",
            content=chat_request.message
        ))
        
        # 获取历史消息
        history_messages = self.get_messages(session_id)
        history = []
        for msg in history_messages[:-1]:  # 排除刚添加的用户消息
            history.append({
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_results": msg.tool_results
            })
        
        # 流式处理
        full_content = ""
        tool_calls = None
        
        async for chunk in agent_service.process_stream(
            chat_request.message, 
            history
        ):
            full_content += chunk["content"]
            if chunk.get("tool_calls"):
                tool_calls = chunk["tool_calls"]
            
            yield {
                "content": chunk["content"],
                "is_final": chunk["is_final"],
                "tool_calls": tool_calls if chunk["is_final"] else None
            }
        
        # 保存完整的Assistant消息
        if full_content:
            self.create_message(MessageCreate(
                session_id=session_id,
                role="assistant",
                content=full_content,
                tool_calls=tool_calls
            ))
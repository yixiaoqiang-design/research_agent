from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.chat import (
    SessionCreate, SessionResponse, ChatRequest, 
    ChatResponse, ChatStreamChunk, MessageResponse
)
from app.services.chat import ChatService
import json

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """创建新的聊天会话"""
    service = ChatService(db)
    session = service.create_session(session_data)
    return session

@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    db: Session = Depends(get_db)
):
    """获取所有聊天会话"""
    service = ChatService(db)
    sessions = service.get_all_sessions()
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取特定会话"""
    service = ChatService(db)
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取会话消息
    messages = service.get_messages(session_id)
    session.messages = messages
    
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """删除会话"""
    service = ChatService(db)
    success = service.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """发送消息（非流式）"""
    if chat_request.stream:
        raise HTTPException(status_code=400, detail="Use /stream endpoint for streaming")
    
    service = ChatService(db)
    result = await service.process_chat(chat_request)
    return ChatResponse(
        session_id=result["session_id"],
        message=result["message"],
        is_complete=True
    )

@router.post("/stream")
async def stream_message_post(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """流式发送消息（POST方法）"""
    if not chat_request.message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    service = ChatService(db)
    
    async def generate():
        try:
            async for chunk in service.process_stream_chat(chat_request):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            logger.error(f"流式处理异常: {e}")
            yield f"data: {json.dumps({'content': f'错误: {str(e)}', 'is_final': True})}\n\n"
        finally:
            # 确保发送结束标记
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*"  # 允许跨域
        }
    )

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取会话的所有消息"""
    service = ChatService(db)
    messages = service.get_messages(session_id)
    return messages


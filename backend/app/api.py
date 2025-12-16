# backend/app/api.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import crud 
from app.schemas import (
    SessionCreate, SessionResponse, ChatRequest, 
    ChatResponse, MessageResponse,
    MessageCreate
)
from app.services import agent_service
import json

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# ====================== 会话管理 ======================

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: Session = Depends(get_db)
):
    """创建新的聊天会话"""
    session = crud.create_session(db, session_data)
    return session

@router.get("/sessions", response_model=List[SessionResponse])
async def get_sessions(
    db: Session = Depends(get_db)
):
    """获取所有聊天会话"""
    sessions = crud.get_all_sessions(db)
    return sessions

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取特定会话"""
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # 获取会话消息
    messages = crud.get_messages(db, session_id)
    session.messages = messages
    
    return session

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: Session = Depends(get_db)
):
    """删除会话"""
    success = crud.delete_session(db, session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}

@router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    db: Session = Depends(get_db)
):
    """获取会话的所有消息"""
    messages = crud.get_messages(db, session_id)
    return messages

# ====================== 消息处理 ======================

@router.post("/message", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """发送消息（非流式）"""
    print ()
    print ('*'*80)
    logger.info("api.py - send_message")
    logger.info("用户发送非流式消息")
    logger.info(f"ChatRequest: {chat_request}")
    if chat_request.stream:
        raise HTTPException(status_code=400, detail="Use /stream endpoint for streaming")
    
    # 如果没有session_id，创建新会话
    session_id = chat_request.session_id
    # 如果没有session_id，则抛出异常
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id不能为空")
    
    # 获取历史消息
    history_messages = crud.get_messages(db, session_id)
    history = []
    for msg in history_messages:
        history.append({
            "role": msg.role,
            "content": msg.content,
            "tool_calls": msg.tool_calls,
            "tool_results": msg.tool_results
        })
    logger.info(f"本会话历史消息数量: {len(history)}")
    
    # 保存用户消息
    logger.info("保存用户消息到数据库")
    user_message = crud.create_message(db, MessageCreate(
        session_id=session_id,
        role="user",
        content=chat_request.message
    ))
    
    # 使用Agent处理消息
    logger.info("调用Agent处理消息")
    agent_response = await agent_service.process_message(
        chat_request.message, 
        history
    )
    
    # 保存Assistant消息
    logger.info("保存Assistant消息到数据库")
    assistant_message = crud.create_message(db, MessageCreate(
        session_id=session_id,
        role="assistant",
        content=agent_response["content"],
        tool_calls=agent_response["tool_calls"],
        tool_results=agent_response["tool_results"]
    ))
    logger.info("Assistant消息保存完成")
    return ChatResponse(
        session_id=session_id,
        message=assistant_message,
        is_complete=True
    )

@router.post("/stream")
async def stream_message_post(
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """流式发送消息（POST方法）"""
    logger.info("Received streaming chat request via POST")
    logger.info(f"ChatRequest: {chat_request}")
    
    if not chat_request.message:
        raise HTTPException(status_code=400, detail="消息不能为空")
    
    # 如果没有session_id，创建新会话
    session_id = chat_request.session_id
    if not session_id:
        session = crud.create_session(db, SessionCreate(title=chat_request.message[:50]))
        session_id = session.id
    
    # 保存用户消息
    user_message = crud.create_message(db, MessageCreate(
        session_id=session_id,
        role="user",
        content=chat_request.message
    ))
    
    # 获取历史消息
    history_messages = crud.get_messages(db, session_id)
    history = []
    for msg in history_messages[:-1]:  # 排除刚添加的用户消息
        history.append({
            "role": msg.role,
            "content": msg.content,
            "tool_calls": msg.tool_calls,
            "tool_results": msg.tool_results
        })
    
    async def generate():
        logger.info("Starting stream generation")
        try:
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
                
                yield f"data: {json.dumps(chunk)}\n\n"
            
            # 保存完整的Assistant消息
            if full_content:
                crud.create_message(db, MessageCreate(
                    session_id=session_id,
                    role="assistant",
                    content=full_content,
                    tool_calls=tool_calls
                ))
                
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

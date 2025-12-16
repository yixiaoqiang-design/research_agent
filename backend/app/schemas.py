from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# 消息基类
class MessageBase(BaseModel):
    role: str  # user, assistant, system, tool
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[Dict[str, Any]] = None

# 消息创建请求
class MessageCreate(MessageBase):
    session_id: str

# 消息响应
class MessageResponse(MessageBase):
    id: str
    session_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# 会话创建请求
class SessionCreate(BaseModel):
    title: Optional[str] = "新对话"

# 会话响应
class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    messages: List[MessageResponse] = []
    
    class Config:
        from_attributes = True

# 聊天请求
class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    stream: Optional[bool] = False

# 聊天响应
class ChatResponse(BaseModel):
    session_id: str
    message: MessageResponse
    is_complete: bool = True

# 流式响应块
class ChatStreamChunk(BaseModel):
    content: str
    is_final: bool = False
    tool_calls: Optional[List[Dict[str, Any]]] = None

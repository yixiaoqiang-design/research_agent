import os
from typing import List, Dict, Any
from langchain_deepseek import ChatDeepSeek
from langchain.agents import create_agent
from langchain_community.agent_toolkits.load_tools import load_tools
from langchain_core.messages import HumanMessage, AIMessage
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class ResearchAgentService:
    """研究助手Agent服务"""
    
    def __init__(self):
        self.agent = None
        self._initialize_agent()
    
    def _initialize_agent(self):
        """初始化Agent"""
        try:
            # 1. 初始化DeepSeek模型
            llm = ChatDeepSeek(
                model=settings.deepseek_model,
                temperature=settings.agent_temperature,
                max_tokens=settings.agent_max_tokens,
                timeout=None,
                max_retries=2,
                api_key=settings.deepseek_api_key,
                base_url=settings.deepseek_base_url
            )
            
            # 2. 加载工具
            tools = load_tools(
                ["arxiv"], 
                llm=llm
            )
            
            # 4. 创建Agent
            system_prompt = """你是一个专业的研究助手，专门帮助用户查找、理解和总结学术论文。
            你可以使用以下工具：
            1. arxiv - 在arXiv上搜索和获取学术论文
            
            请按照以下步骤帮助用户：
            1. 理解用户的研究需求
            2. 使用合适的工具搜索相关论文
            3. 提供论文的关键信息：标题、作者、摘要、关键贡献
            4. 如果用户要求，可以提供论文的详细总结
            5. 保持回答专业、准确、有用
            
            记住：始终用中文回答，除非用户特别要求使用其他语言。
            """
            
            self.agent = create_agent(
                model=llm,
                tools=tools,
                system_prompt=system_prompt
            )
            
            logger.info("Agent初始化成功")
            
        except Exception as e:
            logger.error(f"Agent初始化失败: {e}")
            raise
    
    async def process_message(self, message: str, history: List[Dict] = None) -> Dict[str, Any]:
        """处理用户消息"""
        try:
            if not self.agent:
                self._initialize_agent()
            
            # 准备消息历史
            messages = []
            if history:
                for msg in history:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # 添加当前消息
            messages.append(HumanMessage(content=message))
            
            # 调用Agent
            result = self.agent.invoke({
                "messages": messages
            })
            
            # 提取最后一条消息
            if result and 'messages' in result and result['messages']:
                last_message = result['messages'][-1]
                return {
                    "content": last_message.content,
                    "tool_calls": getattr(last_message, 'tool_calls', None),
                    "tool_results": getattr(last_message, 'tool_results', None)
                }
            else:
                return {"content": "抱歉，我没有收到回复。", "tool_calls": None, "tool_results": None}
                
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return {"content": f"处理消息时出错: {str(e)}", "tool_calls": None, "tool_results": None}
    
    async def process_stream(self, message: str, history: List[Dict] = None):
        """流式处理用户消息（简化版）"""
        try:
            result = await self.process_message(message, history)
            # 模拟流式输出
            content = result["content"]
            for i in range(0, len(content), 10):
                chunk = content[i:i+10]
                yield {
                    "content": chunk,
                    "is_final": i+10 >= len(content),
                    "tool_calls": result["tool_calls"] if i+10 >= len(content) else None
                }
                
        except Exception as e:
            logger.error(f"流式处理失败: {e}")
            yield {"content": f"错误: {str(e)}", "is_final": True, "tool_calls": None}

# 创建全局Agent实例
agent_service = ResearchAgentService()
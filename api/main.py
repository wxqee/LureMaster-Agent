"""
FastAPI 接口层
为未来的小程序/Web 前端提供 API 接口
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid

from agents import LureMasterAgent
from llm import LLMFactory
from tools import ToolManager
from config.settings import get_settings
from api.test_page import router as test_router


# 创建 FastAPI 应用
app = FastAPI(
    title="路亚钓鱼宗师 API",
    description="专业的路亚钓鱼指导助手 API 接口",
    version="1.0.0",
)

# 配置 CORS（允许跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(test_router, prefix="", tags=["测试页面"])

# 会话存储（生产环境应使用 Redis 等）
sessions: Dict[str, LureMasterAgent] = {}


# 请求/响应模型
class ChatRequest(BaseModel):
    """对话请求"""
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    """对话响应"""
    session_id: str
    response: str
    stage: str
    collected_info: Dict[str, Any]


class WeatherRequest(BaseModel):
    """天气查询请求"""
    location: str
    days: Optional[int] = 3


class LocationRequest(BaseModel):
    """地点查询请求"""
    address: str


class KnowledgeRequest(BaseModel):
    """知识检索请求"""
    query: str
    category: Optional[str] = None


# API 路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "路亚钓鱼宗师 API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    settings = get_settings()
    available_llms = LLMFactory.get_available_llms()
    
    return {
        "status": "healthy",
        "mock_mode": settings.mock_mode,
        "available_llms": available_llms,
        "active_sessions": len(sessions),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    对话接口
    
    - 如果不提供 session_id，将创建新会话
    - 返回 Agent 的回复和当前状态
    """
    try:
        # 获取或创建会话
        session_id = request.session_id
        if not session_id or session_id not in sessions:
            session_id = str(uuid.uuid4())
            sessions[session_id] = LureMasterAgent()
        
        agent = sessions[session_id]
        
        # 处理消息
        response = agent.chat(request.message)
        
        # 获取状态
        summary = agent.get_summary()
        
        return ChatResponse(
            session_id=session_id,
            response=response,
            stage=summary["stage"],
            collected_info=summary["collected_info"],
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/session/{session_id}")
async def reset_session(session_id: str):
    """重置会话"""
    if session_id in sessions:
        sessions[session_id].reset()
        return {"status": "reset", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/api/session/{session_id}")
async def get_session_status(session_id: str):
    """获取会话状态"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    agent = sessions[session_id]
    summary = agent.get_summary()
    
    return {
        "session_id": session_id,
        "stage": summary["stage"],
        "collected_info": summary["collected_info"],
        "message_count": summary["message_count"],
    }


@app.post("/api/weather")
async def get_weather(request: WeatherRequest):
    """获取天气信息"""
    tools = ToolManager()
    result = tools.run_tool("weather", location=request.location, days=request.days)
    
    if result.success:
        return result.data
    raise HTTPException(status_code=400, detail=result.error)


@app.post("/api/location")
async def get_location(request: LocationRequest):
    """获取地理信息"""
    tools = ToolManager()
    result = tools.run_tool("location", address=request.address)
    
    if result.success:
        return result.data
    raise HTTPException(status_code=400, detail=result.error)


@app.post("/api/knowledge")
async def search_knowledge(request: KnowledgeRequest):
    """检索知识库"""
    tools = ToolManager()
    result = tools.run_tool("knowledge", query=request.query, category=request.category)
    
    if result.success:
        return result.data
    raise HTTPException(status_code=400, detail=result.error)


@app.get("/api/fish-species")
async def list_fish_species():
    """获取所有鱼种列表"""
    tools = ToolManager()
    knowledge_tool = tools.get_tool("knowledge")
    return knowledge_tool.get_all_fish_species()


@app.get("/api/fishing-spots")
async def list_fishing_spots():
    """获取所有钓点列表"""
    tools = ToolManager()
    knowledge_tool = tools.get_tool("knowledge")
    return knowledge_tool.get_all_spots()


# 启动命令: uvicorn api.main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

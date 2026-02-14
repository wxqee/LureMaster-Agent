"""
简单的 API 测试页面
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json

router = APIRouter()

templates = Jinja2Templates(directory="api/templates")


@router.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """API 测试页面"""
    return templates.TemplateResponse("test.html", {"request": request})


@router.get("/api-list")
async def api_list():
    """获取 API 列表"""
    return {
        "apis": [
            {"method": "GET", "path": "/", "description": "根路径"},
            {"method": "GET", "path": "/health", "description": "健康检查"},
            {"method": "POST", "path": "/api/chat", "description": "对话接口"},
            {"method": "GET", "path": "/api/fish-species", "description": "获取鱼种列表"},
            {"method": "GET", "path": "/api/fishing-spots", "description": "获取钓点列表"},
            {"method": "POST", "path": "/api/weather", "description": "查询天气"},
            {"method": "POST", "path": "/api/knowledge", "description": "检索知识库"},
        ]
    }

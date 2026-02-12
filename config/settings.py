"""
配置管理模块
"""
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """应用配置"""
    
    # LLM API Keys
    dashscope_api_key: Optional[str] = None
    zhipu_api_key: Optional[str] = None
    deepseek_api_key: Optional[str] = None
    
    # 工具 API Keys
    qweather_api_key: Optional[str] = None
    amap_api_key: Optional[str] = None
    
    # 系统配置
    mock_mode: bool = True
    default_llm: str = "qwen"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()

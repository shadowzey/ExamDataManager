"""
应用配置模块
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    """
    # 应用基本信息
    APP_NAME: str = "Excel处理应用"
    API_V1_STR: str = "/api"
    
    # MongoDB 配置
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "excel_app")
    
    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # OpenAI 配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
    OPENAI_PROMPT: str = """你是一个考务费用计算助手。请根据提供的信息计算考务费用。
规则如下：
1. 次数（小时）是指工作的小时数
2. 标准是指每小时的费用标准，单位是元
3. 计算公式为：次数（小时）* 标准 = 金额
4. 请直接返回计算结果，不要有任何解释，只返回数字

例如：
输入：[8, 100]
输出：800
"""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

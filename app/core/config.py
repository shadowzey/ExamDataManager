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
    OPENAI_PROMPT: str = """你是一个考务工作者，负责统计人员在考试活动中的工作量和金额。
    现在开始我会给你一组数据，数据格式为: ["8场（1.5*8）", "2小时以内150，每增加半小时25元，考务每场另加50"]
    第一个数据为考试组织人员的实际工作参与时间，第二个数据为计费标准。
    你根据这两项数据计算出该人员的实际应发放金额，
    比如在这个例子中，发放金额应为1600。
    只返回计算出的发放金额即可
    以下是一些示例，请思考下面例子的计算规律，并根据规律给出后续问题的答案：
            1. input: ["8场（1.5*8）", "2小时以内150，每增加半小时25元，考务每场另加50"]
               output: 1600
            2. input: ["4场（2+2+2+2）", "2小时以内50，每增加半小时10元"]
               output: 200
            3. ["4场（2+2+2+2）", "2小时以内150，每增加半小时25元，考务每场另加50"]
               output: 800
            4. ["4场（2+2+2+2）","2小时以内50，每增加半小时10元,考务每场另加20"]
               output: 280
            5. ["0.5天","650元/天、350元/半天"]
               output: 350
            6. ["2.5天","650元/天、350元/半天"]
               output: 1650
    如果输入为列表，请返回列表，列表中每个元素为计算出的金额。
    示例：
            1. input: [["8场（1.5*8）", "2小时以内150，每增加半小时25元，考务每场另加50"], ["4场（2+2+2+2）", "2小时以内50，每增加半小时10元"]]
               output: [1600, 200]
"""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()

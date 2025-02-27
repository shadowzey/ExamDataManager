"""
FastAPI 主应用程序
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.api import api_router
from app.core.config import settings
from app.core.exception_handlers import add_exception_handlers
from app.db.mongodb import mongodb

# 创建 FastAPI 应用
app = FastAPI(
    title="ExamDataManager",
    description="A comprehensive tool for managing exam data, processing user information, and handling exam venue details",
    version="0.1.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源，生产环境应该限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册异常处理器
add_exception_handlers(app)

# 注册路由
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.on_event("startup")
async def startup_db_client():
    """
    应用启动时连接数据库
    """
    await mongodb.connect_to_database()


@app.on_event("shutdown")
async def shutdown_db_client():
    """
    应用关闭时断开数据库连接
    """
    await mongodb.close_database_connection()


@app.get("/")
async def root():
    """
    根路由，返回应用信息
    """
    return {
        "app": "Excel处理应用",
        "version": "0.1.0",
        "status": "运行中"
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点
    
    用于监控系统是否正常运行
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "message": "系统运行正常"
    }
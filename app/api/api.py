"""
API 路由模块
"""
from fastapi import APIRouter
from app.api.endpoints import employees, excel

# 创建主路由
api_router = APIRouter()

# 添加各个模块的路由
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(excel.router, prefix="/excel", tags=["excel"])

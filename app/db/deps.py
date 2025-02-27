"""
数据库依赖模块
"""
from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.mongodb import mongodb


async def get_employee_collection() -> AsyncIOMotorCollection:
    """
    获取员工集合的依赖函数
    
    用于在路由函数中注入员工集合
    """
    return mongodb.employee_collection

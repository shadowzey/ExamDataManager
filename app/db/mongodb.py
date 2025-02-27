"""
MongoDB 数据库连接模块
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


class MongoDB:
    """
    MongoDB 连接管理类
    
    负责创建和管理 MongoDB 数据库连接
    """
    client: AsyncIOMotorClient = None
    db = None
    employee_collection = None

    async def connect_to_database(self):
        """
        连接到 MongoDB 数据库
        """
        self.client = AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        self.employee_collection = self.db.get_collection("employee_collection")
    
    async def close_database_connection(self):
        """
        关闭 MongoDB 数据库连接
        """
        if self.client:
            self.client.close()


# 创建全局数据库实例
mongodb = MongoDB()

"""
员工服务模块
"""
from typing import Dict, List, Any, Optional, Tuple
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from app.core.exceptions import BadRequestException, NotFoundException


async def get_employee_by_id(
    collection: AsyncIOMotorCollection, 
    employee_id: str
) -> Optional[Dict[str, Any]]:
    """
    根据ID获取员工信息
    
    Args:
        collection: 员工集合
        employee_id: 员工ID
        
    Returns:
        员工信息字典，如果未找到则返回None
    """
    try:
        object_id = ObjectId(employee_id)
    except Exception:
        raise BadRequestException(f"无效的员工ID格式: {employee_id}")
    
    employee = await collection.find_one({"_id": object_id})
    if employee:
        employee["_id"] = str(employee["_id"])
    return employee


async def get_employees_by_name(
    collection: AsyncIOMotorCollection, 
    name: str
) -> List[Dict[str, Any]]:
    """
    根据姓名查询员工
    
    Args:
        collection: 员工集合
        name: 员工姓名
        
    Returns:
        匹配的员工列表
    """
    if not name or len(name.strip()) == 0:
        raise BadRequestException("员工姓名不能为空")
    
    cursor = collection.find({"name": name})
    employees = []
    
    async for employee in cursor:
        employee["_id"] = str(employee["_id"])
        employees.append(employee)
    
    return employees


async def create_employee(
    collection: AsyncIOMotorCollection, 
    employee_data: Dict[str, Any]
) -> str:
    """
    创建新员工
    
    Args:
        collection: 员工集合
        employee_data: 员工数据
        
    Returns:
        创建的员工ID
    """
    if not employee_data:
        raise BadRequestException("员工数据不能为空")
    
    if not employee_data.get("name"):
        raise BadRequestException("员工姓名不能为空")
    
    # 检查是否已存在同名员工
    existing = await collection.find_one({"name": employee_data["name"]})
    if existing:
        # 返回警告信息，但仍然允许创建
        # 可以在此处添加日志记录
        pass
    
    result = await collection.insert_one(employee_data)
    return str(result.inserted_id)


async def update_employee(
    collection: AsyncIOMotorCollection, 
    employee_id: str, 
    employee_data: Dict[str, Any]
) -> bool:
    """
    更新员工信息
    
    Args:
        collection: 员工集合
        employee_id: 员工ID
        employee_data: 更新的员工数据
        
    Returns:
        是否成功更新
    """
    if not employee_data:
        raise BadRequestException("更新数据不能为空")
    
    try:
        object_id = ObjectId(employee_id)
    except Exception:
        raise BadRequestException(f"无效的员工ID格式: {employee_id}")
    
    # 移除_id字段，防止尝试更新主键
    if "_id" in employee_data:
        del employee_data["_id"]
    
    result = await collection.update_one(
        {"_id": object_id},
        {"$set": employee_data}
    )
    
    return result.modified_count > 0


async def delete_employee(
    collection: AsyncIOMotorCollection, 
    employee_id: str
) -> bool:
    """
    删除员工
    
    Args:
        collection: 员工集合
        employee_id: 员工ID
        
    Returns:
        是否成功删除
    """
    try:
        object_id = ObjectId(employee_id)
    except Exception:
        raise BadRequestException(f"无效的员工ID格式: {employee_id}")
    
    result = await collection.delete_one({"_id": object_id})
    return result.deleted_count > 0

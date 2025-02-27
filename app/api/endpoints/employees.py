"""
员工相关 API 端点
"""
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.deps import get_employee_collection
from app.services import employee_service
from app.core.responses import Response, ListResponse
from app.core.exceptions import NotFoundException, BadRequestException

router = APIRouter()


@router.get("/{employee_id}", response_model=Response[Dict[str, Any]])
async def get_employee(
    employee_id: str,
    collection: AsyncIOMotorCollection = Depends(get_employee_collection)
) -> Response:
    """
    获取员工信息
    
    根据员工ID获取员工详细信息
    
    Args:
        employee_id: 员工ID
        collection: 员工集合依赖注入
        
    Returns:
        员工信息
    """
    employee = await employee_service.get_employee_by_id(collection, employee_id)
    if not employee:
        raise NotFoundException(f"未找到ID为 {employee_id} 的员工")
    return Response(data=employee)


@router.get("/name/{name}", response_model=ListResponse[Dict[str, Any]])
async def get_employee_by_name(
    name: str,
    collection: AsyncIOMotorCollection = Depends(get_employee_collection)
) -> ListResponse:
    """
    根据姓名查询员工
    
    Args:
        name: 员工姓名
        collection: 员工集合依赖注入
        
    Returns:
        匹配的员工列表
    """
    employees = await employee_service.get_employees_by_name(collection, name)
    return ListResponse(
        data=employees,
        total=len(employees)
    )


@router.post("/@create", response_model=Response[Dict[str, str]])
async def create_employee(
    employee: Dict[str, Any],
    collection: AsyncIOMotorCollection = Depends(get_employee_collection)
) -> Response:
    """
    创建新员工
    
    Args:
        employee: 员工数据
        collection: 员工集合依赖注入
        
    Returns:
        操作状态
    """
    if not employee.get("name"):
        raise BadRequestException("员工姓名不能为空")
    
    result = await employee_service.create_employee(collection, employee)
    return Response(
        message="员工创建成功",
        data={"id": result}
    )


@router.put("/{employee_id}", response_model=Response[Dict[str, str]])
async def update_employee(
    employee_id: str,
    employee: Dict[str, Any],
    collection: AsyncIOMotorCollection = Depends(get_employee_collection)
) -> Response:
    """
    更新员工信息
    
    Args:
        employee_id: 员工ID
        employee: 更新的员工数据
        collection: 员工集合依赖注入
        
    Returns:
        操作状态
    """
    if not employee:
        raise BadRequestException("更新数据不能为空")
    
    result = await employee_service.update_employee(collection, employee_id, employee)
    if not result:
        raise NotFoundException(f"未找到ID为 {employee_id} 的员工")
    
    return Response(
        message="员工信息更新成功",
        data={"id": employee_id}
    )


@router.delete("/{employee_id}", response_model=Response[Dict[str, str]])
async def delete_employee(
    employee_id: str,
    collection: AsyncIOMotorCollection = Depends(get_employee_collection)
) -> Response:
    """
    删除员工
    
    Args:
        employee_id: 员工ID
        collection: 员工集合依赖注入
        
    Returns:
        操作状态
    """
    result = await employee_service.delete_employee(collection, employee_id)
    if not result:
        raise NotFoundException(f"未找到ID为 {employee_id} 的员工")
    
    return Response(
        message="员工删除成功",
        data={"id": employee_id}
    )

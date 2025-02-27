"""
标准响应模型模块
"""
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union
from pydantic import BaseModel, Field


class ResponseBase(BaseModel):
    """
    API响应基础模型
    
    所有API响应的基础结构，包含状态码、消息和数据
    """
    code: int = Field(200, description="状态码")
    message: str = Field("操作成功", description="响应消息")
    success: bool = Field(True, description="操作是否成功")


T = TypeVar('T')


class Response(ResponseBase, Generic[T]):
    """
    通用API响应模型
    
    包含任意类型的数据负载
    """
    data: Optional[T] = Field(None, description="响应数据")


class ListResponse(ResponseBase, Generic[T]):
    """
    列表类型API响应模型
    
    包含列表类型的数据负载和总数
    """
    data: List[T] = Field([], description="响应数据列表")
    total: int = Field(0, description="数据总数")


class ErrorResponse(ResponseBase):
    """
    错误响应模型
    
    用于返回错误信息
    """
    code: int = Field(400, description="错误状态码")
    message: str = Field("操作失败", description="错误消息")
    success: bool = Field(False, description="操作是否成功")
    detail: Optional[str] = Field(None, description="详细错误信息")


# 预定义的错误响应
VALIDATION_ERROR = ErrorResponse(
    code=422,
    message="数据验证错误",
    detail="提交的数据无效"
)

NOT_FOUND_ERROR = ErrorResponse(
    code=404,
    message="资源不存在",
    detail="请求的资源不存在"
)

INTERNAL_SERVER_ERROR = ErrorResponse(
    code=500,
    message="服务器内部错误",
    detail="服务器处理请求时发生错误"
)

UNAUTHORIZED_ERROR = ErrorResponse(
    code=401,
    message="未授权访问",
    detail="请先进行身份验证"
)

FORBIDDEN_ERROR = ErrorResponse(
    code=403,
    message="禁止访问",
    detail="没有权限访问该资源"
)

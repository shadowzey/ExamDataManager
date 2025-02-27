"""
异常处理模块
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class APIException(HTTPException):
    """
    API异常基类
    
    所有自定义API异常的基类，继承自FastAPI的HTTPException
    """
    def __init__(
        self,
        status_code: int,
        detail: str = None,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundException(APIException):
    """
    资源不存在异常
    """
    def __init__(self, detail: str = "请求的资源不存在"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class BadRequestException(APIException):
    """
    错误请求异常
    """
    def __init__(self, detail: str = "请求参数无效"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


class InternalServerException(APIException):
    """
    服务器内部错误异常
    """
    def __init__(self, detail: str = "服务器内部错误"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


class UnauthorizedException(APIException):
    """
    未授权异常
    """
    def __init__(self, detail: str = "未授权访问"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class ForbiddenException(APIException):
    """
    禁止访问异常
    """
    def __init__(self, detail: str = "禁止访问该资源"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ValidationException(APIException):
    """
    数据验证异常
    """
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)

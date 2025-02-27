"""
全局异常处理器模块
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.core.exceptions import APIException
from app.core.responses import ErrorResponse


def add_exception_handlers(app: FastAPI) -> None:
    """
    添加全局异常处理器到FastAPI应用
    
    Args:
        app: FastAPI应用实例
    """
    
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
        """
        处理自定义API异常
        """
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                code=exc.status_code,
                message=str(exc.detail),
                detail=str(exc.detail)
            ).dict()
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """
        处理请求验证异常
        """
        errors = []
        for error in exc.errors():
            error_msg = f"{'.'.join(str(loc) for loc in error['loc'])}: {error['msg']}"
            errors.append(error_msg)
        
        error_detail = "; ".join(errors)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="请求数据验证失败",
                detail=error_detail
            ).dict()
        )
    
    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
        """
        处理Pydantic验证异常
        """
        errors = []
        for error in exc.errors():
            error_msg = f"{'.'.join(str(loc) for loc in error['loc'])}: {error['msg']}"
            errors.append(error_msg)
        
        error_detail = "; ".join(errors)
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                message="数据验证失败",
                detail=error_detail
            ).dict()
        )
    
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        处理未捕获的异常
        """
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message="服务器内部错误",
                detail=str(exc)
            ).dict()
        )

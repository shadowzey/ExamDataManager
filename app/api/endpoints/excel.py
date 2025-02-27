"""
Excel 处理相关 API 端点
"""
import uuid
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, File, UploadFile, BackgroundTasks, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
from motor.motor_asyncio import AsyncIOMotorCollection
from app.db.deps import get_employee_collection
from app.services import fee_service
from app.utils.excel import read_excel_to_dict_list_async, write_dict_list_to_excel
from app.core.exceptions import BadRequestException, InternalServerException

router = APIRouter()

# 存储任务进度的字典
tasks_progress = {}


@router.post("/upload/{sheet_name}")
async def upload_file(
    sheet_name: str,
    file: UploadFile = File(...),
    collection: AsyncIOMotorCollection = Depends(get_employee_collection),
    background_tasks: BackgroundTasks = None
) -> StreamingResponse:
    """
    上传并处理 Excel 文件
    
    上传 Excel 文件，处理指定工作表中的数据，并返回处理后的 Excel 文件
    
    Args:
        sheet_name: 要处理的工作表名称
        file: 上传的 Excel 文件
        collection: 员工集合依赖注入
        background_tasks: 后台任务管理器
        
    Returns:
        处理后的 Excel 文件作为流式响应
    """
    # 验证文件类型
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise BadRequestException("只支持Excel文件格式（.xls或.xlsx）")
    
    try:
        # 读取上传的文件内容
        contents = await file.read()
        
        # 更新进度
        task_id = str(uuid.uuid4())
        tasks_progress[task_id] = {"status": "reading", "progress": 10}
        
        # 将 Excel 文件内容转换为字典列表 (使用异步版本)
        data_dict_list = await read_excel_to_dict_list_async(contents, sheet_name)
        
        if not data_dict_list:
            raise BadRequestException(f"工作表 '{sheet_name}' 为空或不存在")
        
        # 更新进度
        tasks_progress[task_id] = {"status": "processing", "progress": 40}
        
        # 补充费用信息
        fee_result, repeat_list, no_match_list = await fee_service.supplement_fee_info(
            collection, data_dict_list
        )
        
        # 更新进度
        tasks_progress[task_id] = {"status": "writing", "progress": 70}
        
        # 将处理后的数据写入新的 Excel 文件 (使用异步版本)
        excel_data = await write_dict_list_to_excel(fee_result, sheet_name, repeat_list, no_match_list)
        
        # 更新进度
        tasks_progress[task_id] = {"status": "completed", "progress": 100}
        
        # 添加清理文件的后台任务（如果提供了background_tasks）
        if background_tasks and hasattr(file, "file"):
            background_tasks.add_task(lambda: file.file.close())
            # 添加清理进度信息的后台任务
            background_tasks.add_task(lambda: tasks_progress.pop(task_id, None))
        
        # 返回处理后的 Excel 文件
        return StreamingResponse(
            iter([excel_data]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename=processed_{file.filename}",
                "X-Task-ID": task_id  # 在响应头中包含任务ID
            }
        )
    except BadRequestException as e:
        # 重新抛出请求错误异常
        raise
    except Exception as e:
        # 记录详细错误信息
        import traceback
        error_details = traceback.format_exc()
        print(f"处理文件时出错: {error_details}")
        # 将其他异常转换为内部服务器错误
        raise InternalServerException(f"处理文件时出错: {str(e)}")


@router.post("/upload-async/{sheet_name}")
async def upload_file_async(
    sheet_name: str,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    collection: AsyncIOMotorCollection = Depends(get_employee_collection)
) -> Dict[str, Any]:
    """
    异步上传并处理 Excel 文件
    
    上传 Excel 文件，在后台处理指定工作表中的数据，并返回任务ID用于跟踪进度
    
    Args:
        sheet_name: 要处理的工作表名称
        file: 上传的 Excel 文件
        background_tasks: 后台任务管理器
        collection: 员工集合依赖注入
        
    Returns:
        包含任务ID的响应
    """
    # 验证文件类型
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise BadRequestException("只支持Excel文件格式（.xls或.xlsx）")
    
    # 生成任务ID
    task_id = str(uuid.uuid4())
    tasks_progress[task_id] = {"status": "pending", "progress": 0}
    
    # 读取上传的文件内容
    contents = await file.read()
    
    # 添加后台任务处理Excel文件
    background_tasks.add_task(
        process_excel_file_background,
        task_id,
        contents,
        sheet_name,
        collection,
        file.filename
    )
    
    return {
        "success": True,
        "message": "文件上传成功，正在后台处理",
        "data": {
            "task_id": task_id
        }
    }


@router.get("/task/{task_id}")
async def get_task_progress(task_id: str) -> Dict[str, Any]:
    """
    获取任务进度
    
    根据任务ID获取Excel处理任务的进度
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务进度信息
    """
    if task_id not in tasks_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在或已完成"
        )
    
    return {
        "success": True,
        "data": tasks_progress[task_id]
    }


@router.get("/download/{task_id}")
async def download_processed_file(task_id: str) -> StreamingResponse:
    """
    下载处理后的文件
    
    根据任务ID下载处理完成的Excel文件
    
    Args:
        task_id: 任务ID
        
    Returns:
        处理后的Excel文件
    """
    if task_id not in tasks_progress:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"任务 {task_id} 不存在或已完成"
        )
    
    task_info = tasks_progress[task_id]
    
    if task_info["status"] != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"任务尚未完成，当前状态: {task_info['status']}, 进度: {task_info['progress']}%"
        )
    
    if "result" not in task_info:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="任务结果不可用"
        )
    
    # 返回处理后的Excel文件
    return StreamingResponse(
        iter([task_info["result"]]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={task_info['filename']}"}
    )


async def process_excel_file_background(
    task_id: str,
    contents: bytes,
    sheet_name: str,
    collection: AsyncIOMotorCollection,
    original_filename: str
) -> None:
    """
    在后台处理Excel文件
    
    Args:
        task_id: 任务ID
        contents: Excel文件内容
        sheet_name: 工作表名称
        collection: 数据库集合
        original_filename: 原始文件名
    """
    try:
        # 更新进度 - 读取阶段
        tasks_progress[task_id] = {"status": "reading", "progress": 10}
        
        # 将Excel文件内容转换为字典列表
        data_dict_list = await read_excel_to_dict_list_async(contents, sheet_name)
        
        if not data_dict_list:
            tasks_progress[task_id] = {
                "status": "error", 
                "progress": 0, 
                "error": f"工作表 '{sheet_name}' 为空或不存在"
            }
            return
        
        # 更新进度 - 处理阶段
        tasks_progress[task_id] = {"status": "processing", "progress": 40}
        
        # 补充费用信息
        fee_result, repeat_list, no_match_list = await fee_service.supplement_fee_info(
            collection, data_dict_list
        )
        
        # 更新进度 - 写入阶段
        tasks_progress[task_id] = {"status": "writing", "progress": 70}
        
        # 将处理后的数据写入新的Excel文件
        excel_data = await write_dict_list_to_excel(fee_result, sheet_name, repeat_list, no_match_list)
        
        # 更新进度 - 完成
        tasks_progress[task_id] = {
            "status": "completed", 
            "progress": 100,
            "result": excel_data,
            "filename": f"processed_{original_filename}"
        }
        
    except Exception as e:
        # 记录详细错误信息
        import traceback
        error_details = traceback.format_exc()
        print(f"后台处理文件时出错: {error_details}")
        
        # 更新任务状态为错误
        tasks_progress[task_id] = {
            "status": "error",
            "progress": 0,
            "error": str(e)
        }

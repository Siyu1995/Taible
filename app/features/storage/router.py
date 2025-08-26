"""存储功能路由模块

提供文件上传相关的API端点
"""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.shared.schemas import APIResponse

from .models import (
    FileRecordRead,
    FileRecordUpdate,
    PresignedUrlRequest,
    PresignedUrlResponse,
)
from .service import storage_service


router = APIRouter()


@router.post(
    "/presigned-upload-url",
    response_model=APIResponse[PresignedUrlResponse],
    summary="获取预签名上传URL",
    description="生成用于文件上传的预签名URL，客户端可使用此URL直接上传文件到R2存储"
)
async def get_presigned_upload_url(
    request: PresignedUrlRequest,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[PresignedUrlResponse]:
    """获取预签名上传URL
    
    创建文件记录并生成预签名URL，允许客户端直接上传文件到Cloudflare R2
    
    Args:
        request: 预签名URL请求数据
        db: 数据库会话
        
    Returns:
        APIResponse[PresignedUrlResponse]: 包含预签名URL的响应
        
    Raises:
        HTTPException: 当生成预签名URL失败时
    """
    try:
        logger.info(f"请求预签名上传URL: {request.filename} ({request.file_size} bytes)")
        
        response = await storage_service.create_presigned_upload_request(db, request)
        
        return APIResponse(
            success=True,
            data=response,
            message="预签名上传URL生成成功",
            code=200
        )
        
    except Exception as e:
        logger.error(f"生成预签名上传URL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成预签名上传URL失败: {str(e)}"
        )


@router.get(
    "/files/{file_id}",
    response_model=APIResponse[FileRecordRead],
    summary="获取文件记录",
    description="根据文件ID获取文件的元数据信息"
)
async def get_file_record(
    file_id: int,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[FileRecordRead]:
    """获取文件记录
    
    Args:
        file_id: 文件记录ID
        db: 数据库会话
        
    Returns:
        APIResponse[FileRecordRead]: 文件记录信息
        
    Raises:
        HTTPException: 当文件不存在时
    """
    try:
        file_record = await storage_service.get_file_record(db, file_id)
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件记录不存在: {file_id}"
            )
        
        return APIResponse(
            success=True,
            data=FileRecordRead.model_validate(file_record),
            message="获取文件记录成功",
            code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文件记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件记录失败: {str(e)}"
        )


@router.patch(
    "/files/{file_id}",
    response_model=APIResponse[FileRecordRead],
    summary="更新文件记录",
    description="更新文件记录的状态等信息"
)
async def update_file_record(
    file_id: int,
    update_data: FileRecordUpdate,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[FileRecordRead]:
    """更新文件记录
    
    Args:
        file_id: 文件记录ID
        update_data: 更新数据
        db: 数据库会话
        
    Returns:
        APIResponse[FileRecordRead]: 更新后的文件记录
        
    Raises:
        HTTPException: 当文件不存在时
    """
    try:
        updated_record = await storage_service.update_file_record(
            db, file_id, update_data
        )
        
        if not updated_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件记录不存在: {file_id}"
            )
        
        return APIResponse(
            success=True,
            data=FileRecordRead.model_validate(updated_record),
            message="文件记录更新成功",
            code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新文件记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新文件记录失败: {str(e)}"
        )


@router.get(
    "/files/{file_id}/download-url",
    response_model=APIResponse[Dict[str, Any]],
    summary="获取文件下载URL",
    description="生成用于文件下载的预签名URL"
)
async def get_file_download_url(
    file_id: int,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[Dict[str, Any]]:
    """获取文件下载URL
    
    Args:
        file_id: 文件记录ID
        db: 数据库会话
        
    Returns:
        APIResponse[Dict[str, Any]]: 包含下载URL的响应
        
    Raises:
        HTTPException: 当文件不存在时
    """
    try:
        file_record = await storage_service.get_file_record(db, file_id)
        
        if not file_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件记录不存在: {file_id}"
            )
        
        if file_record.upload_status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件尚未上传完成"
            )
        
        download_url = await storage_service.generate_presigned_download_url(
            file_record.file_key
        )
        
        return APIResponse(
            success=True,
            data={
                "download_url": download_url,
                "filename": file_record.filename,
                "expires_in": 3600
            },
            message="下载URL生成成功",
            code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成下载URL失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成下载URL失败: {str(e)}"
        )


@router.post(
    "/files/{file_id}/complete",
    response_model=APIResponse[FileRecordRead],
    summary="标记文件上传完成",
    description="客户端上传完成后调用此接口标记文件状态为已完成"
)
async def mark_upload_complete(
    file_id: int,
    db: AsyncSession = Depends(get_db)
) -> APIResponse[FileRecordRead]:
    """标记文件上传完成
    
    Args:
        file_id: 文件记录ID
        db: 数据库会话
        
    Returns:
        APIResponse[FileRecordRead]: 更新后的文件记录
        
    Raises:
        HTTPException: 当文件不存在时
    """
    try:
        update_data = FileRecordUpdate(upload_status="completed")
        updated_record = await storage_service.update_file_record(
            db, file_id, update_data
        )
        
        if not updated_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"文件记录不存在: {file_id}"
            )
        
        logger.info(f"文件上传已完成: {file_id} - {updated_record.filename}")
        
        return APIResponse(
            success=True,
            data=FileRecordRead.model_validate(updated_record),
            message="文件上传完成",
            code=200
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"标记上传完成失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记上传完成失败: {str(e)}"
        )
"""存储服务模块

提供Cloudflare R2对象存储操作和预签名URL生成
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import settings
from app.core.redis import cache_result, redis_manager

from .models import (
    FileRecord,
    FileRecordCreate,
    FileRecordUpdate,
    PresignedUrlRequest,
    PresignedUrlResponse,
)


class R2StorageService:
    """Cloudflare R2存储服务
    
    提供文件上传、下载和管理功能
    """
    
    def __init__(self) -> None:
        """初始化R2存储服务
        
        创建boto3客户端连接到Cloudflare R2
        """
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=settings.endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.region_name,
            )
            
            # 默认存储桶名称（从endpoint URL提取）
            self.bucket_name = "taible-storage"
            
            logger.info(f"R2存储服务已初始化，端点: {settings.endpoint_url}")
            
        except Exception as e:
            logger.error(f"R2存储服务初始化失败: {e}")
            raise
    
    def _generate_file_key(self, filename: str) -> str:
        """生成唯一的文件存储键名
        
        格式: uploads/{year}/{month}/{uuid}_{filename}
        
        Args:
            filename: 原始文件名
            
        Returns:
            str: 文件存储键名
        """
        now = datetime.utcnow()
        unique_id = str(uuid.uuid4())
        
        # 清理文件名，移除特殊字符
        clean_filename = "".join(c for c in filename if c.isalnum() or c in ".-_")
        
        return f"uploads/{now.year}/{now.month:02d}/{unique_id}_{clean_filename}"
    
    async def create_file_record(
        self, 
        db: AsyncSession, 
        file_data: FileRecordCreate
    ) -> FileRecord:
        """创建文件记录
        
        在数据库中创建文件元数据记录
        
        Args:
            db: 数据库会话
            file_data: 文件创建数据
            
        Returns:
            FileRecord: 创建的文件记录
        """
        file_key = self._generate_file_key(file_data.filename)
        
        file_record = FileRecord(
            filename=file_data.filename,
            file_key=file_key,
            file_size=file_data.file_size,
            content_type=file_data.content_type,
            upload_status="pending"
        )
        
        db.add(file_record)
        await db.commit()
        await db.refresh(file_record)
        
        logger.info(f"文件记录已创建: {file_record.id} - {file_record.filename}")
        return file_record
    
    async def get_file_record(
        self, 
        db: AsyncSession, 
        file_id: int
    ) -> Optional[FileRecord]:
        """获取文件记录
        
        Args:
            db: 数据库会话
            file_id: 文件记录ID
            
        Returns:
            Optional[FileRecord]: 文件记录，不存在返回None
        """
        statement = select(FileRecord).where(FileRecord.id == file_id)
        result = await db.execute(statement)
        return result.scalar_one_or_none()
    
    async def update_file_record(
        self,
        db: AsyncSession,
        file_id: int,
        update_data: FileRecordUpdate
    ) -> Optional[FileRecord]:
        """更新文件记录
        
        Args:
            db: 数据库会话
            file_id: 文件记录ID
            update_data: 更新数据
            
        Returns:
            Optional[FileRecord]: 更新后的文件记录
        """
        file_record = await self.get_file_record(db, file_id)
        if not file_record:
            return None
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(file_record, field, value)
        
        await db.commit()
        await db.refresh(file_record)
        
        logger.info(f"文件记录已更新: {file_id}")
        return file_record
    
    @cache_result("storage", ttl=300)  # 缓存5分钟
    async def generate_presigned_upload_url(
        self,
        file_key: str,
        content_type: str,
        expires_in: int = 3600
    ) -> str:
        """生成预签名上传URL
        
        Args:
            file_key: 文件存储键名
            content_type: 文件MIME类型
            expires_in: URL过期时间（秒），默认1小时
            
        Returns:
            str: 预签名上传URL
            
        Raises:
            ClientError: R2服务错误
            NoCredentialsError: 认证错误
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': content_type,
                },
                ExpiresIn=expires_in
            )
            
            logger.info(f"预签名上传URL已生成: {file_key}")
            return presigned_url
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"生成预签名URL失败: {e}")
            raise
    
    @cache_result("storage", ttl=300)  # 缓存5分钟
    async def generate_presigned_download_url(
        self,
        file_key: str,
        expires_in: int = 3600
    ) -> str:
        """生成预签名下载URL
        
        Args:
            file_key: 文件存储键名
            expires_in: URL过期时间（秒），默认1小时
            
        Returns:
            str: 预签名下载URL
            
        Raises:
            ClientError: R2服务错误
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                },
                ExpiresIn=expires_in
            )
            
            logger.info(f"预签名下载URL已生成: {file_key}")
            return presigned_url
            
        except ClientError as e:
            logger.error(f"生成预签名下载URL失败: {e}")
            raise
    
    async def check_file_exists(self, file_key: str) -> bool:
        """检查文件是否存在于R2存储中
        
        Args:
            file_key: 文件存储键名
            
        Returns:
            bool: 文件是否存在
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.error(f"检查文件存在失败: {e}")
            raise
    
    async def delete_file(self, file_key: str) -> bool:
        """删除R2存储中的文件
        
        Args:
            file_key: 文件存储键名
            
        Returns:
            bool: 是否删除成功
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            logger.info(f"文件已删除: {file_key}")
            return True
        except ClientError as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    async def create_presigned_upload_request(
        self,
        db: AsyncSession,
        request: PresignedUrlRequest
    ) -> PresignedUrlResponse:
        """创建预签名上传请求
        
        完整流程：创建文件记录 -> 生成预签名URL -> 返回响应
        
        Args:
            db: 数据库会话
            request: 预签名URL请求
            
        Returns:
            PresignedUrlResponse: 预签名URL响应
        """
        # 创建文件记录
        file_data = FileRecordCreate(
            filename=request.filename,
            file_size=request.file_size,
            content_type=request.content_type
        )
        
        file_record = await self.create_file_record(db, file_data)
        
        # 生成预签名上传URL
        expires_in = 3600  # 1小时过期
        upload_url = await self.generate_presigned_upload_url(
            file_record.file_key,
            request.content_type,
            expires_in
        )
        
        return PresignedUrlResponse(
            upload_url=upload_url,
            file_key=file_record.file_key,
            expires_in=expires_in,
            file_record_id=file_record.id
        )


# 全局存储服务实例
storage_service = R2StorageService()
"""存储功能数据模型

定义文件上传相关的数据模型
"""

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class FileRecord(SQLModel, table=True):
    """文件记录表
    
    存储上传文件的元数据信息
    """
    
    __tablename__ = "file_records"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="文件记录ID")
    filename: str = Field(max_length=255, description="原始文件名")
    file_key: str = Field(max_length=500, unique=True, description="R2存储键名")
    file_size: int = Field(description="文件大小（字节）")
    content_type: str = Field(max_length=100, description="文件MIME类型")
    upload_status: str = Field(
        default="pending", 
        max_length=20, 
        description="上传状态: pending, completed, failed"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    
    class Config:
        """模型配置"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileRecordCreate(SQLModel):
    """创建文件记录的请求模型"""
    
    filename: str = Field(max_length=255, description="原始文件名")
    file_size: int = Field(gt=0, description="文件大小（字节）")
    content_type: str = Field(max_length=100, description="文件MIME类型")


class FileRecordRead(SQLModel):
    """文件记录响应模型"""
    
    id: int
    filename: str
    file_key: str
    file_size: int
    content_type: str
    upload_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class FileRecordUpdate(SQLModel):
    """更新文件记录的请求模型"""
    
    upload_status: Optional[str] = Field(default=None, description="上传状态")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="更新时间")


class PresignedUrlRequest(SQLModel):
    """预签名URL请求模型"""
    
    filename: str = Field(max_length=255, description="文件名")
    content_type: str = Field(max_length=100, description="文件MIME类型")
    file_size: int = Field(gt=0, le=100*1024*1024, description="文件大小（字节），最大100MB")


class PresignedUrlResponse(SQLModel):
    """预签名URL响应模型"""
    
    upload_url: str = Field(description="预签名上传URL")
    file_key: str = Field(description="文件存储键名")
    expires_in: int = Field(description="URL过期时间（秒）")
    file_record_id: int = Field(description="文件记录ID")
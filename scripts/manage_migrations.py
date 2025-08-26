#!/usr/bin/env python3
"""数据库迁移管理脚本

提供便捷的 Alembic 迁移管理命令
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger


class MigrationManager:
    """数据库迁移管理器
    
    封装 Alembic 命令，提供更友好的迁移管理接口
    """
    
    def __init__(self):
        """初始化迁移管理器"""
        self.project_root = Path(__file__).parent.parent
        self.alembic_ini = self.project_root / "alembic.ini"
        
        # 检查 alembic.ini 是否存在
        if not self.alembic_ini.exists():
            raise FileNotFoundError(f"找不到 alembic.ini 文件: {self.alembic_ini}")
    
    def _run_alembic_command(self, command: list[str]) -> bool:
        """运行 Alembic 命令
        
        Args:
            command: Alembic 命令列表
            
        Returns:
            bool: 命令是否执行成功
        """
        try:
            # 切换到项目根目录
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout:
                print(result.stdout)
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Alembic 命令执行失败: {' '.join(command)}")
            logger.error(f"错误输出: {e.stderr}")
            if e.stdout:
                logger.error(f"标准输出: {e.stdout}")
            return False
        except Exception as e:
            logger.error(f"执行命令时出错: {e}")
            return False
    
    def init_migrations(self) -> bool:
        """初始化迁移环境
        
        创建初始迁移文件
        
        Returns:
            bool: 是否成功
        """
        logger.info("初始化数据库迁移环境...")
        
        # 检查是否已经初始化
        versions_dir = self.project_root / "alembic" / "versions"
        if versions_dir.exists() and list(versions_dir.glob("*.py")):
            logger.warning("迁移环境已经初始化，跳过初始化步骤")
            return True
        
        # 创建初始迁移
        return self.create_migration("初始化数据库结构")
    
    def create_migration(self, message: str) -> bool:
        """创建新的迁移文件
        
        Args:
            message: 迁移描述信息
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"创建新迁移: {message}")
        
        command = ["alembic", "revision", "--autogenerate", "-m", message]
        return self._run_alembic_command(command)
    
    def upgrade_database(self, revision: str = "head") -> bool:
        """升级数据库到指定版本
        
        Args:
            revision: 目标版本，默认为最新版本 (head)
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"升级数据库到版本: {revision}")
        
        command = ["alembic", "upgrade", revision]
        return self._run_alembic_command(command)
    
    def downgrade_database(self, revision: str) -> bool:
        """降级数据库到指定版本
        
        Args:
            revision: 目标版本
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"降级数据库到版本: {revision}")
        
        command = ["alembic", "downgrade", revision]
        return self._run_alembic_command(command)
    
    def show_current_revision(self) -> bool:
        """显示当前数据库版本
        
        Returns:
            bool: 是否成功
        """
        logger.info("查询当前数据库版本...")
        
        command = ["alembic", "current"]
        return self._run_alembic_command(command)
    
    def show_migration_history(self) -> bool:
        """显示迁移历史
        
        Returns:
            bool: 是否成功
        """
        logger.info("查询迁移历史...")
        
        command = ["alembic", "history", "--verbose"]
        return self._run_alembic_command(command)
    
    def show_pending_migrations(self) -> bool:
        """显示待执行的迁移
        
        Returns:
            bool: 是否成功
        """
        logger.info("查询待执行的迁移...")
        
        command = ["alembic", "heads"]
        return self._run_alembic_command(command)
    
    def stamp_database(self, revision: str) -> bool:
        """标记数据库版本（不执行迁移）
        
        用于将现有数据库标记为特定版本，通常用于初始化已存在的数据库
        
        Args:
            revision: 要标记的版本
            
        Returns:
            bool: 是否成功
        """
        logger.info(f"标记数据库版本为: {revision}")
        
        command = ["alembic", "stamp", revision]
        return self._run_alembic_command(command)


def print_usage():
    """打印使用说明"""
    print("""
数据库迁移管理脚本

用法:
    python scripts/manage_migrations.py <command> [args]

命令:
    init                    - 初始化迁移环境
    create <message>        - 创建新迁移
    upgrade [revision]      - 升级数据库（默认到最新版本）
    downgrade <revision>    - 降级数据库到指定版本
    current                 - 显示当前数据库版本
    history                 - 显示迁移历史
    pending                 - 显示待执行的迁移
    stamp <revision>        - 标记数据库版本（不执行迁移）

示例:
    python scripts/manage_migrations.py init
    python scripts/manage_migrations.py create "添加用户表"
    python scripts/manage_migrations.py upgrade
    python scripts/manage_migrations.py downgrade -1
    python scripts/manage_migrations.py current
    """)


def main():
    """主函数"""
    # 配置日志
    logger.remove()  # 移除默认处理器
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    try:
        manager = MigrationManager()
        
        if command == "init":
            success = manager.init_migrations()
        elif command == "create":
            if len(sys.argv) < 3:
                logger.error("请提供迁移描述信息")
                sys.exit(1)
            message = " ".join(sys.argv[2:])
            success = manager.create_migration(message)
        elif command == "upgrade":
            revision = sys.argv[2] if len(sys.argv) > 2 else "head"
            success = manager.upgrade_database(revision)
        elif command == "downgrade":
            if len(sys.argv) < 3:
                logger.error("请提供目标版本")
                sys.exit(1)
            revision = sys.argv[2]
            success = manager.downgrade_database(revision)
        elif command == "current":
            success = manager.show_current_revision()
        elif command == "history":
            success = manager.show_migration_history()
        elif command == "pending":
            success = manager.show_pending_migrations()
        elif command == "stamp":
            if len(sys.argv) < 3:
                logger.error("请提供要标记的版本")
                sys.exit(1)
            revision = sys.argv[2]
            success = manager.stamp_database(revision)
        else:
            logger.error(f"未知命令: {command}")
            print_usage()
            sys.exit(1)
        
        if success:
            logger.info("✅ 操作完成")
        else:
            logger.error("❌ 操作失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
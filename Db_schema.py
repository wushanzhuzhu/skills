# 这个文件现在作为数据库模式定义的入口点
# 保持向后兼容性
from models.mysql_schema import db_schema_manager

# 提供向后兼容的接口
dbmcp = db_schema_manager.register_resources()

# 也可以直接使用数据库模式管理器
__all__ = ['dbmcp', 'db_schema_manager']
# config.py
class Config:
    # MySQL数据库连接信息
    MYSQL_HOST = '178.106.97.230'    # 数据库主机地址（本地为127.0.0.1）
    MYSQL_PORT = 3306           # 数据库端口（默认3306）
    MYSQL_USER = 'wushan'         # 数据库用户名（根据实际情况修改）
    MYSQL_PASSWORD = 'W1203293s!'   # 数据库密码（根据实际情况修改）
    MYSQL_DB = 'flask_mysql_api'# 数据库名（与前文创建的一致）
    MYSQL_CHARSET = 'utf8mb4'   # 字符集

# 开发环境配置（继承Config）
class DevelopmentConfig(Config):
    DEBUG = True  # 开启调试模式

# 生产环境配置（继承Config）
class ProductionConfig(Config):
    DEBUG = False  # 关闭调试模式
    # 生产环境可添加数据库连接池配置，提升性能
    MYSQL_POOL_SIZE = 10
    MYSQL_MAX_OVERFLOW = 20

# 配置映射，方便切换环境
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


# 项目配置
DEFAULT_SSH_PORT = 22
DEFAULT_SSH_USER = "cloud"
DEFAULT_SSH_KEY_PATH = "./id_rsa_cloud"

# 安超平台默认凭据
DEFAULT_PLATFORM_USER = "admin"
DEFAULT_PLATFORM_PASSWORD = "Admin@123"

# 虚拟机默认配置
DEFAULT_VM_CONFIG = {
    "cpu": 2,
    "memory": 4,
    "size": 80,
    "haEnable": True,
    "priority": 1,
    "rebuildPriority": 3,
    "cloneType": "LINK",
    "audioType": "ich6"
}

# 数据库配置
DB_CONFIG = {
    "default_user": "root",
    "default_password": "cloudadmin#Passw0rd"
}

# 存储配置
STORAGE_PAGE_SIZES = ["4K", "8K", "16K", "32K"]
COMPRESSION_TYPES = ["Disabled", "LZ4", "Gzip_opt", "Gzip_high"]
VIDEO_MODELS = ["cirrus", "qxl", "virtio", "vga"]

# 数据库表配置
SUPPORTED_TABLES = [
    "virtual_machine",
    "virtual_disk",
    "virtual_network",
    "storage_pool"
]
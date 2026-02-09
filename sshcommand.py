import paramiko
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

import time
def ssh_execute_command(hostname, port, username, key_path, command):
    """通过SSH密钥执行远程命令
    Args:
        hostname: 远程主机IP或域名
        port: SSH端口（默认22）
        username: 登录用户名
        key_path: 私钥文件路径
        command: 要执行的命令
    """
    result = ""
    ssh = paramiko.SSHClient()
    try:
        # 自动添加主机密钥（生产环境建议使用WarningPolicy）
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # 加载私钥并建立连接
        private_key = paramiko.RSAKey.from_private_key_file(key_path)
        ssh.connect(
            hostname=hostname,
            port=port,
            username=username,
            pkey=private_key,
            timeout=30
        )

        # 执行命令并获取结果
        stdin, stdout, stderr = ssh.exec_command(command,get_pty=True)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        logger.info("命令输出:")
        logger.info(output or "无输出")
        result = output

        if error:
            logger.info("错误信息:")
            logger.info(error)

    except paramiko.AuthenticationException:
        logger.info("认证失败：请检查密钥路径和服务器配置")
    except paramiko.SSHException as e:
        logger.info(f"SSH连接异常: {str(e)}")
    except Exception as e:
        logger.info(f"执行异常: {str(e)}")
    finally:
        ssh.close()
    return result
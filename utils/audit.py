import requests
import urllib3
import sys
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 尝试导入自定义模块，如果失败则使用默认实现
try:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from TestCaseApp.clonetest import encodePass
except ImportError as e:
    logger.warning(f"无法导入 TestCaseApp.clonetest.encodePass: {e}")
    logger.warning("使用默认密码处理方式")
    
    def encodePass(password: str) -> str:
        """
        默认密码处理函数
        注意：这只是一个示例实现，实际应用中应该使用安全的加密算法
        """
        return password  # 实际应用中应替换为合适的加密实现

import ssl

# 全局禁用SSL验证
ssl._create_default_https_context = ssl._create_unverified_context
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ArcherAudit:
    def __init__(self, username: str, password: str, url: str):
        """初始化配置参数"""
        self.base_url = url  # API基础地址
        self.session = requests.Session()
        self.auth_token = None
        self.timeout = 20 * 60  # 20分钟超时时间
        self.session.verify = False  # 禁用SSL验证
        self.username = username
        self.password = password
        urllib3.disable_warnings()

    def setSession(self) -> bool:
        """
        POST登录接口，返回认证token并设置会话头和Cookie
        包含：
        - Authorization: Bearer Token
        - Cookie: sessionId=xxx; userId=xxx
        """
        login_url = f"{self.base_url}/api/resource/login"
        
        try:
            encoded_password = encodePass(self.password)
            logger.info("密码已处理")
        except Exception as e:
            logger.error(f"密码处理失败: {e}")
            return False
            
        payload = {
            "loginName": self.username,
            "password": encoded_password,  # 使用密码加密方法
            "loginType": "front"
        }

        try:
            response = self.session.post(login_url, json=payload, verify=False, timeout=self.timeout)
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {e}")
            return False

        logger.info(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                logger.info(f"响应数据: {response_data}")
                
                self.auth_token = response_data.get("token")
                data = response_data.get("data", {})
                session_id = data.get("sessionId")
                user_id = data.get("userId")
                
                if not session_id or not user_id:
                    logger.error("响应中缺少必要的sessionId或userId")
                    return False
                    
                logger.info(f"sessionId: {session_id}")
                logger.info(f"user_id: {user_id}")

                # 设置认证头
                auth_header = {
                    "Authorization": f"Bearer {self.auth_token}",
                    "Content-Type": "application/json"
                }
                self.session.headers.update(auth_header)

                # 设置Cookie
                self.session.cookies.set("sessionId", session_id)
                self.session.cookies.set("userId", user_id)

                logger.info("登录成功")
                return True
            except ValueError as e:
                logger.error(f"解析JSON响应失败: {e}")
                return False
        else:
            logger.error(f"HTTP请求失败，状态码: {response.status_code}")
            try:
                logger.error(f"错误响应: {response.json()}")
            except ValueError:
                logger.error(f"错误内容: {response.text}")
            return False
    
if __name__ == "__main__":
    audit = ArcherAudit("admin", "Admin@123", "https://172.118.57.100")
    audit.setSession()
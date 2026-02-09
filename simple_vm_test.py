#!/usr/bin/env python3
"""
简单虚拟机创建测试
"""

import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

import time
from pathlib import Path

# 添加主项目路径
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from utils.audit import ArcherAudit
from Hosts import Hosts
from Instances import Instances

def simple_vm_test():
    """简单虚拟机创建测试"""
    logger.info("🚀 开始简单虚拟机创建测试")
    
    # 1. 连接认证
    audit = ArcherAudit("admin", "Admin@123", "https://172.118.57.100")
    audit.setSession()
    
    # 2. 初始化客户端
    host = Hosts("admin", "Admin@123", "https://172.118.57.100", audit)
    instances = Instances("admin", "Admin@123", "https://172.118.57.100", audit)
    
    # 3. 获取存储信息
    stors = host.getStorsbyDiskType()
    if not stors:
        logger.error("❌ 无法获取存储信息")
        return
    
    storage = stors[0]
    zone_id = host.zone
    
    logger.info(f"✅ 存储: {storage['stackName']}, 区域: {zone_id[:8]}...")
    
    # 4. 尝试创建最简虚拟机
    vm_name = f"simple-vm-{int(time.time())}"
    
    try:
        # 手动构建最小payload
        payload = {
            "name": vm_name,
            "hostname": vm_name, 
            "cpu": 2,
            "memory": 4,
            "zoneId": zone_id,
            "imageId": "dc46978b-7ddf-433b-ba0a-7accab96f22d",  # Windows镜像
            "adminPassword": "Admin@123456",
            "disk": [{
                "storageManageId": storage['storageManageId'],
                "size": 20,
                "diskType": storage['diskType']
            }]
        }
        
        logger.info(f"📋 简化payload: {payload}")
        
        # 直接调用API
        url = f"{instances.base_url}/api/resource/createVirtualMachine"
        response = instances.session.post(url, json=payload, verify=False)
        response_data = response.json()
        logger.info(f"📝 API响应: {response_data}")
        
        if response.status_code == 200 and response_data.get('code') == 0:
            result = response_data.get('data', {}).get('ids', [])
            logger.info(f"🎉 创建结果: {result}")
        else:
            logger.error(f"❌ API错误: {response_data.get('errorMessage', '未知错误')}")
            result = None
        
        logger.info(f"🎉 创建结果: {result}")
        
        if result:
            logger.info(f"✅ 虚拟机创建成功: {result}")
        else:
            logger.error("❌ 虚拟机创建失败")
            
    except Exception as e:
        logger.error(f"❌ 创建异常: {str(e)}")

if __name__ == "__main__":
    simple_vm_test()
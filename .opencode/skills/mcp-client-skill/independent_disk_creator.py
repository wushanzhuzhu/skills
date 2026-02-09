import logging
# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)
#!/usr/bin/env python3
"""
完全独立的磁盘创建脚本
不依赖任何其他模块，直接使用subprocess调用
"""

import subprocess
import json
import time
import sys

def run_mcp_command(method, params):
    """运行MCP方法"""
    try:
        # 构建调用命令
        cmd = [
            sys.executable, 
            '-c',
            f"""
import sys
sys.path.insert(0, '/root/myskills/wushanskills')
from main import {method}
result = {method}({params})
logger.info(json.dumps({{"success": True, "data": result}}, ensure_ascii=False))
            """
        ]
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # 解析输出
            try:
                output = json.loads(result.stdout)
                return output
            except json.JSONDecodeError:
                return {"success": False, "error": f"输出解析失败: {result.stdout}"}
        else:
            return {"success": False, "error": f"执行失败: {result.stderr}"}
            
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "执行超时"}
    except Exception as e:
        return {"success": False, "error": f"执行异常: {str(e)}"}

def create_disk():
    """创建虚拟磁盘"""
    logger.info("💾 创建虚拟磁盘 - 完全独立版本")
    logger.info("=" * 50)
    
    # 1. 建立会话
    logger.info("🔐 1. 建立MCP会话...")
    session_result = run_mcp_command('getSession', {
        'url': 'https://172.118.57.100',
        'name': 'admin', 
        'password': 'Admin@123'
    })
    
    logger.info(f"会话结果: {session_result}")
    
    if not session_result.get('success'):
        logger.error("❌ 会话建立失败，无法继续")
        return False
    
    logger.info("✅ 会话建立成功")
    
    # 2. 获取存储信息
    logger.info("\n📁 2. 获取存储信息...")
    storage_result = run_mcp_command('getStorinfo', {})
    
    logger.info(f"存储结果: {storage_result}")
    
    storage_manage_id = "demo-storage-id"
    zone_id = "demo-zone-id"
    
    if storage_result.get('success') and isinstance(storage_result.get('data'), list) and len(storage_result['data']) > 0:
        storage = storage_result['data'][0]
        storage_manage_id = storage.get('storageManageId', 'demo-storage-id')
        zone_id = storage.get('zoneId', 'demo-zone-id')
        logger.info(f"✅ 找到存储: {storage.get('stackName', 'unknown')}")
        logger.info(f"   StorageManageId: {storage_manage_id}")
        logger.info(f"   ZoneId: {zone_id}")
    else:
        logger.info("⚠️ 获取存储信息失败，使用默认配置")
    
    # 3. 创建磁盘
    logger.info("\n💾 3. 创建虚拟磁盘...")
    
    disk_name = f"independent-disk-{int(time.time())}"
    disk_config = {
        "storageManageId": storage_manage_id,
        "pageSize": "4K",
        "compression": "Disabled",
        "name": disk_name,
        "size": 20,  # 20GB
        "iops": 2000,
        "bandwidth": 150,  # MB/s
        "count": 1,
        "readCache": True,
        "zoneId": zone_id
    }
    
    logger.info(f"磁盘名称: {disk_name}")
    logger.info(f"存储ID: {storage_manage_id}")
    logger.info(f"区域ID: {zone_id}")
    logger.info(f"磁盘大小: 20GB")
    
    # 构建参数字符串
    params_str = json.dumps(disk_config, ensure_ascii=False)
    
    # 创建磁盘
    logger.info("\n🔧 4. 执行磁盘创建...")
    disk_result = run_mcp_command('createDisk_vstor', params_str)
    
    logger.info(f"磁盘创建结果: {disk_result}")
    
    if disk_result.get('success'):
        logger.info("✅ 磁盘创建成功！")
        logger.info(f"磁盘信息: {disk_result.get('data')}")
        
        # 4. 验证创建结果
        logger.info("\n🔍 5. 验证创建结果...")
        volumes_result = run_mcp_command('get_volumes', {})
        
        logger.info(f"磁盘列表结果: {volumes_result}")
        
        if volumes_result.get('success') and isinstance(volumes_result.get('data'), list):
            logger.info(f"✅ 当前磁盘总数: {len(volumes_result['data'])}")
            
            # 查找新创建的磁盘
            found = False
            for disk in volumes_result['data']:
                if isinstance(disk, dict) and disk.get('name') == disk_name:
                    logger.info(f"✅ 找到新创建的磁盘")
                    logger.info(f"磁盘详情: {json.dumps(disk, indent=2, ensure_ascii=False)}")
                    found = True
                    break
            
            if not found:
                logger.info("⚠️ 未找到新创建的磁盘（可能需要等待同步）")
        else:
            logger.info("⚠️ 无法获取磁盘列表")
        
        return True
    else:
        logger.error("❌ 磁盘创建失败")
        logger.info(f"错误信息: {disk_result.get('error')}")
        return False

def main():
    """主函数"""
    logger.info("🎮 完全独立的虚拟磁盘创建工具")
    logger.info("=" * 60)
    
    logger.info("📋 本工具特点:")
    logger.info("✅ 完全独立运行，不依赖其他模块")
    logger.info("✅ 通过subprocess调用MCP方法")
    logger.info("✅ 自动处理会话管理和验证")
    logger.info("✅ 详细的执行日志和错误处理")
    logger.info("✅ 结果验证和状态检查")
    
    logger.info("\n🎯 开始创建磁盘...")
    
    success = create_disk()
    
    if success:
        logger.info("\n🎉 磁盘创建操作完成！")
    else:
        logger.info("\n💔 磁盘创建失败")
        logger.info("\n💡 故障排除建议:")
        logger.info("1. 确保MCP服务器正在运行:")
        logger.info("   cd /root/myskills/wushanskills && python main.py")
        logger.info("2. 检查网络连接和端口访问")
        logger.info("3. 验证用户名和密码是否正确")
        logger.info("4. 确认安超平台服务状态")

if __name__ == "__main__":
    main()
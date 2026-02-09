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
MCP Client Skill 测试脚本
测试Skill调用MCP Server方法的功能
"""

import sys
import json
import os
from pathlib import Path

# 添加技能路径
skill_path = Path(__file__).parent
sys.path.insert(0, str(skill_path))

def test_session_manager():
    """测试会话管理器"""
    logger.info("🧪 测试会话管理器...")
    
    try:
        from session_manager import SessionManager
        
        # 创建会话管理器
        session_mgr = SessionManager()
        
        # 测试环境配置
        environments = session_mgr.get_available_environments()
        logger.info(f"📋 可用环境数量: {len(environments)}")
        
        if environments:
            env_id = list(environments.keys())[0]
            logger.info(f"🌐 测试环境: {env_id}")
            
            # 测试会话健康检查
            health = session_mgr.check_session_health()
            logger.info(f"🏥 会话健康状态: {health}")
            
            logger.info("✅ 会话管理器测试通过")
        else:
            logger.info("⚠️ 没有可用环境，跳过会话测试")
            
    except Exception as e:
        logger.error(f"❌ 会话管理器测试失败: {e}")
        return False
    
    return True

def test_mcp_method_client():
    """测试MCP方法客户端"""
    logger.info("\n🧪 测试MCP方法客户端...")
    
    try:
        from mcp_method_client import MCPMethodClient
        
        # 创建MCP客户端
        mcp_client = MCPMethodClient(auto_session=False)  # 禁用自动会话用于测试
        
        # 测试方法注册
        methods = mcp_client.get_available_methods()
        logger.info(f"📋 注册的MCP方法数量: {len(methods)}")
        
        # 显示前几个方法
        for method_name, method_info in list(methods.items())[:3]:
            logger.info(f"   - {method_name}: {method_info['description']}")
        
        # 测试方法信息获取
        if 'get_audit' in methods:
            info = mcp_client.get_method_info('get_audit')
            logger.info(f"📊 get_audit方法信息: {info.get('description')}")
        
        logger.info("✅ MCP方法客户端测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP方法客户端测试失败: {e}")
        return False

def test_mcp_client_skill():
    """测试主技能类"""
    logger.info("\n🧪 测试MCP客户端技能...")
    
    try:
        from mcp_client_skill import MCPClientSkill
        
        # 创建技能实例（禁用自动会话）
        skill = MCPClientSkill(env_id=None, auto_session=False)
        
        # 测试获取客户端信息
        info = skill.get_mcp_client_info()
        logger.info(f"📊 技能信息:")
        logger.info(f"   - 可用方法数量: {len(info.get('available_methods', []))}")
        logger.info(f"   - 调用统计: {info.get('call_statistics', {})}")
        
        logger.info("✅ MCP客户端技能测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ MCP客户端技能测试失败: {e}")
        return False

def test_error_handler():
    """测试错误处理器"""
    logger.info("\n🧪 测试错误处理器...")
    
    try:
        from utils.error_handler import ErrorHandler, handle_error
        
        # 创建错误处理器
        error_handler = ErrorHandler()
        
        # 测试错误分类
        test_errors = [
            Exception("connection failed"),
            Exception("session not found"),
            Exception("authentication failed"),
            Exception("parameter validation failed")
        ]
        
        for error in test_errors:
            error_info = error_handler.classify_error(error)
            logger.info(f"   - {error_info.category.value}: {error_info.message}")
        
        # 测试错误处理
        result = handle_error(Exception("test error"))
        logger.info(f"📊 错误处理结果: {result.get('error', {}).get('category')}")
        
        logger.info("✅ 错误处理器测试通过")
        return True
        
    except Exception as e:
        logger.error(f"❌ 错误处理器测试失败: {e}")
        return False

def test_config_loading():
    """测试配置加载"""
    logger.info("\n🧪 测试配置加载...")
    
    try:
        config_path = skill_path / "config" / "scenarios.json"
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            scenarios = config.get('scenarios', {})
            logger.info(f"📋 配置场景数量: {len(scenarios)}")
            
            for scenario_name, scenario_config in list(scenarios.items())[:2]:
                logger.info(f"   - {scenario_name}: {scenario_config.get('description')}")
            
            logger.info("✅ 配置加载测试通过")
        else:
            logger.info("⚠️ 配置文件不存在，跳过配置测试")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ 配置加载测试失败: {e}")
        return False

def test_skill_structure():
    """测试技能结构完整性"""
    logger.info("\n🧪 测试技能结构完整性...")
    
    required_files = [
        "SKILL.md",
        "mcp_client_skill.py",
        "mcp_method_client.py", 
        "session_manager.py",
        "config/scenarios.json",
        "utils/error_handler.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = skill_path / file_path
        if not full_path.exists():
            missing_files.append(file_path)
    
    if missing_files:
        logger.error(f"❌ 缺少文件: {missing_files}")
        return False
    
    logger.info(f"✅ 所有必需文件都存在 ({len(required_files)} 个)")
    return True

def main():
    """主测试函数"""
    logger.info("🚀 MCP Client Skill 功能测试")
    logger.info("=" * 50)
    
    # 检查技能结构
    structure_ok = test_skill_structure()
    
    if not structure_ok:
        logger.error("❌ 技能结构不完整，无法继续测试")
        return
    
    # 运行各项测试
    tests = [
        ("配置加载", test_config_loading),
        ("会话管理器", test_session_manager),
        ("MCP方法客户端", test_mcp_method_client),
        ("错误处理器", test_error_handler),
        ("主技能类", test_mcp_client_skill)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            logger.error(f"❌ {test_name}测试异常: {e}")
    
    # 测试结果汇总
    logger.info("\n" + "=" * 50)
    logger.info("📊 测试结果汇总:")
    logger.info(f"   总测试数: {total_tests}")
    logger.info(f"   通过测试: {passed_tests}")
    logger.info(f"   失败测试: {total_tests - passed_tests}")
    logger.info(f"   成功率: {passed_tests/total_tests*100:.1f}%")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有测试都通过了！MCP Client Skill 已准备就绪")
    else:
        logger.info("⚠️ 部分测试失败，请检查相关功能")
    
    logger.info("\n💡 使用提示:")
    logger.info("   python mcp_client_skill.py --command interactive  # 进入交互模式")
    logger.info("   python mcp_client_skill.py --command health       # 系统健康检查")
    logger.info("   python mcp_client_skill.py --command resources    # 资源管理概览")
    logger.info("   python mcp_client_skill.py --command info          # 客户端信息")

if __name__ == "__main__":
    main()
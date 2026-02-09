---
name: vm-tools
description: 批量创建虚拟机实例，支持环境感知、智能配置和多种部署策略
license: MIT
compatibility: opencode
metadata:
  audience: vm-admins
  workflow: vm-management
  version: "1.0"
  author: "OpenCode Assistant"
---

## 核心功能

### 🌐 环境管理
- **环境配置**: 存储在 `environments.json` 文件中，包含IP、用户名、密码
- **环境选择**: 支持多环境选择，默认环境配置
- **连接验证**: 测试环境可达性和资源发现

### 🎯 批量虚拟机创建
- **批量创建**: 一次性创建1-50个虚拟机实例
- **智能命名**: 支持序列命名、模板命名、自定义命名
- **实时反馈**: 分步创建进度跟踪，成功/失败统计

### ⚙️ 智能配置管理
- **CPU/内存配置**: 核心数、插槽数、内存大小
- **存储配置**: 磁盘大小、类型、压缩方式
- **网络配置**: 视频模型、克隆类型
- **高可用配置**: HA启用、优先级、重建策略
- **高级配置**: NUMA、大页内存、气球内存

### 🖼️ 镜像智能管理
- **镜像发现**: 自动获取可用镜像列表
- **智能推荐**: 基于用例推荐最适合的镜像
- **兼容性检查**: 镜像格式和兼容性验证

### ✅ 完整性验证
- **API参数检查**: 验证参数范围和合法性
- **资源可用性**: 检查CPU、内存、存储资源
- **配置验证**: 模板和自定义配置验证

## 配置模板

| 模板名称 | CPU | 内存 | 磁盘 | HA | 用途 |
|---------|-----|------|------|----|-----|
| basic | 2核 | 4GB | 80GB | 否 | 办公开发、轻量服务 |
| web_server | 4核 | 8GB | 100GB | 是 | Web应用、API服务 |
| database | 8核 | 16GB | 200GB | 是 | MySQL、PostgreSQL数据库 |
| development | 2核 | 4GB | 60GB | 否 | 代码开发、功能测试 |
| high_performance | 16核 | 32GB | 500GB | 是 | 大数据处理、AI计算 |
| container_host | 8核 | 16GB | 150GB | 是 | Docker、Kubernetes节点 |

## 使用方式

### 本地脚本执行（推荐）
```bash
# 列出可用环境和模板
python .opencode/skills/vm-tools/vm_creator.py --list-env
python .opencode/skills/vm-tools/vm_creator.py --list-templates

# 快速创建示例
python .opencode/skills/vm-tools/vm_creator.py --env production --count 3 --template web_server

# 高级用法 - 自定义参数
python .opencode/skills/vm-tools/vm_creator.py \
  --env production \
  --count 5 \
  --template database \
  --cpu 8 \
  --memory 16 \
  --disk 200
```

### Skill交互式使用
- 询问创建需求（数量、环境、配置）
- 智能推荐模板和参数
- 提供创建进度和结果统计



## 环境配置要求

### 环境配置文件
```json
{
  "environments": {
    "production": {
      "url": "https://172.118.57.100",
      "username": "admin", 
      "password": "Admin@123",
      "description": "生产环境"
    }
  }
}
```

---

**开始使用：直接告诉我您的VM创建需求，我将智能配置并为您执行批量创建！**
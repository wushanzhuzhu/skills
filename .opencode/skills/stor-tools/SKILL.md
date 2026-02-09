---
name: stor-tools
description: 安超平台存储集群管理专家，提供Zookeeper监控、磁盘健康检查、存储使用分析和异常告警功能
license: MIT
compatibility: opencode
metadata:
  audience: storage-admins
  workflow: storage-management
  version: "1.0"
  author: "OpenCode Assistant"
---

## 核心功能

### 🐘 Zookeeper监控
- **集群状态**: `docker exec -it mxsp zklist -c` 显示Zookeeper集群信息
- **节点监控**: 实时监控Zookeeper节点状态
- **连接检查**: 验证客户端连接状态

### 💿 磁盘健康检查
- **不可访问磁盘**: `docker exec -it mxsp showInodes --stale` 检查不可访问的磁盘
- **磁盘状态**: 全面检查磁盘健康状态
- **故障预警**: 自动识别潜在磁盘问题

### 📊 存储使用分析
- **磁盘占用**: `docker exec -it mxsp mxServices -n <node_id> -L` 显示节点磁盘占用情况
- **容量规划**: 提供存储容量趋势分析
- **性能监控**: 监控IOPS和带宽使用情况

### ⚠️ 异常告警
- **实时告警**: 自动检测存储异常并告警
- **问题定位**: 提供详细的问题定位信息
- **解决建议**: 针对常见问题提供解决方案

## 使用方式

### 本地脚本执行（推荐）
```bash
# 检查Zookeeper集群状态
python .opencode/skills/stor-tools/storage_manager.py --env production --zk-status

# 检查磁盘健康状态
python .opencode/skills/stor-tools/storage_manager.py --env production --disk-health

# 查看存储使用情况
python .opencode/skills/stor-tools/storage_manager.py --env production --usage --node 5

# 完整存储状态检查
python .opencode/skills/stor-tools/storage_manager.py --env production --check-all

# 监控特定存储节点
python .opencode/skills/stor-tools/storage_manager.py --env production --node 5 --detail
```

### Skill交互式使用
- 询问具体需求（集群状态/磁盘检查/容量分析）
- 智能选择检查范围和深度
- 提供详细的分析报告和优化建议



## 安全配置

### Docker执行
- **容器权限**: 使用适当的Docker权限执行命令
- **安全上下文**: 确保在安全的环境中执行存储操作

### SSH认证
- **密钥文件**: `/root/myskills/SKILLS/id_rsa_cloud`
- **用户名**: `cloud` (具有Docker和存储管理权限)
- **连接方式**: RSA密钥认证

---

**开始使用：直接告诉我您需要检查的存储信息，我将为您提供专业的存储管理服务！**
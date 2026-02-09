---
name: platform-monitor
description: 安超平台监控专家，提供日志分析、资源监控、健康检查和性能分析功能
license: MIT
compatibility: opencode
metadata:
  audience: platform-admins
  workflow: platform-monitoring
  version: "1.0"
  author: "OpenCode Assistant"
---

## 核心功能

### 📝 日志分析
- **云管平台日志**: `/var/log/haihe/resource/resource.log` 分析资源服务日志
- **错误统计**: 统计最近错误和警告数量
- **异常检测**: 自动识别异常模式和问题
- **日志搜索**: 支持关键词和时间范围搜索

### 📈 资源监控
- **CPU使用率**: 实时监控各节点CPU使用情况
- **内存使用率**: 内存占用和剩余容量监控
- **存储使用率**: 磁盘空间使用情况
- **网络流量**: 网络带宽使用和连接数监控

### 🔍 健康检查
- **组件状态**: API、数据库、消息队列等组件状态
- **服务可用性**: 各服务响应时间和可用性检查
- **集群状态**: 整个平台的集群健康状态
- **依赖检查**: 检查各组件间的依赖关系

### ⚡ 性能分析
- **性能趋势**: 资源使用趋势分析
- **瓶颈识别**: 识别系统性能瓶颈
- **容量规划**: 基于历史数据的容量预测
- **优化建议**: 提供性能优化建议

## 使用方式

### 本地脚本执行（推荐）
```bash
# 查看平台整体状态
python .opencode/skills/platform-monitor/platform_monitor.py --env production --status

# 分析平台日志
python .opencode/skills/platform-monitor/platform_monitor.py --env production --log-analysis

# 监控资源使用
python .opencode/skills/platform-monitor/platform_monitor.py --env production --resource-monitor

# 执行完整健康检查
python .opencode/skills/platform-monitor/platform_monitor.py --env production --health-check

# 实时监控模式
python .opencode/skills/platform-monitor/platform_monitor.py --env production --real-time --interval 60
```

### Skill交互式使用
- 询问监控需求（状态检查/日志分析/性能监控）
- 智能选择监控范围和深度
- 提供详细的监控报告和告警信息



## 安全配置

### 日志访问
- **日志路径**: `/var/log/haihe/resource/resource.log`
- **访问权限**: 需要适当的日志读取权限
- **敏感信息**: 自动过滤敏感信息（密码、密钥等）

### 系统监控
- **权限要求**: 需要系统监控权限
- **SSH认证**: 使用 `/root/myskills/SKILLS/id_rsa_cloud` 密钥
- **用户权限**: `cloud` 用户具有监控权限

---

**开始使用：直接告诉我您需要监控的平台信息，我将为您提供专业的监控分析服务！**
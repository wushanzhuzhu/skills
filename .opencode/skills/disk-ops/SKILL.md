---
name: disk-ops
description: 批量创建虚拟磁盘，支持可定制参数和智能命名策略。当需要快速部署存储资源、批量创建测试环境磁盘、或标准化磁盘配置时使用此技能。支持1-100个磁盘的批量创建，提供多种配置模板和完整的参数自定义。
---

# Disk Ops

## 核心功能

### 🎯 批量磁盘创建
- **批量创建**: 一次性创建1-100个虚拟磁盘
- **实时反馈**: 详细的进度跟踪和结果汇总
- **智能延迟**: 1秒间隔避免API频率限制

### ⚙️ 参数自定义
- **存储管理ID**: 选择目标存储管理器
- **页面大小**: 4K/8K/16K/32K
- **数据压缩**: 禁用/LZ4/Gzip_opt/Gzip_high
- **磁盘大小**: 灵活的GB大小设置
- **性能参数**: IOPS（75-250000）、带宽（1-1000 MB/s）
- **读缓存**: 可选的读缓存开关
- **区域选择**: 指定存储区域

### 🏷️ 智能命名策略
- **顺序命名**: prefix-0、prefix-1、prefix-2...
- **时间戳命名**: disk-20250130-001、disk-20250130-002...
- **UUID命名**: volume-{uuid}

### ✅ 完整性保证
- **API参数检查**: 验证参数范围和合法性
- **资源可用性**: 检查存储资源和配额
- **命名冲突检测**: 自动检测和解决命名冲突

## 使用方式

### 本地脚本执行（推荐）
```bash
# 查看可用环境和模板
python .opencode/skills/disk-ops/disk_creator.py --list-env
python .opencode/skills/disk-ops/disk_creator.py --list-templates

# 快速创建示例
python .opencode/skills/disk-ops/disk_creator.py --env production --size 10
python .opencode/skills/disk-ops/disk_creator.py --env production --size 50 --count 3 --template performance

# 高级用法 - 自定义参数
python .opencode/skills/disk-ops/disk_creator.py \
  --env production \
  --size 20 \
  --name my-custom-disk \
  --template basic \
  --iops 800 \
  --bandwidth 120 \
  --read-cache

# 批量创建示例
python .opencode/skills/disk-ops/disk_creator.py \
  --env production \
  --size 100 \
  --count 5 \
  --template storage \
  --name backup-disk
```

### Skill交互式使用
- 询问创建需求（数量、大小、用途）
- 智能推荐参数组合
- 提供创建进度和结果统计

## 配置模板

| 模板名称 | 页面大小 | 压缩方式 | IOPS | 带宽 | 读缓存 | 适用场景 |
|---------|---------|----------|------|------|--------|---------|
| basic | 4K | 禁用 | 100 | 50 | 否 | 轻量应用 |
| performance | 8K | LZ4 | 5000 | 200 | 是 | 数据库 |
| storage | 16K | Gzip_opt | 1000 | 100 | 是 | 文件存储 |
| test | 4K | 禁用 | 100 | 50 | 否 | 测试环境 |

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

## 错误处理

### 常见问题处理
- **参数限制错误**: 自动调整到有效值
- **存储资源不足**: 提供替代方案
- **命名冲突**: 自动添加时间戳后缀
- **部分创建失败**: 继续创建其他磁盘

---

**开始使用：直接告诉我您的磁盘创建需求，我将智能配置并为您执行批量创建！**

# 您的Skills清单（已完成同步）

## 🎯 您有 **5个skills**：

1. **disk-tools** - 创建、查询、管理虚拟磁盘
2. **node-tools** - 管理宿主机  
3. **stor-tools** - 管理存储集群
4. **stack-tools** - 管理虚拟化节点
5. **vm-tools** - 创建虚拟机

## 🛠️ 双重配置：

### 📁 真正的skill目录 (`.opencode/skills/`)
- `disk-tools/` ← 重命名完成
- `node-tools/` ← 重命名完成
- `stor-tools/` ← 重命名完成
- `stack-tools/` ← 重命名完成
- `vm-tools/` ← 重命名完成

### 📄 调用脚本 (项目根目录)
- `skill_disk_tools.py`
- `skill_node_tools.py`
- `skill_stor_tools.py`
- `skill_stack_tools.py`
- `skill_vm_tools.py`

## 🚀 使用示例：
```bash
python skill_disk_tools.py --env 172.118.57.100 --template performance --size 50 --count 5
python skill_disk_tools.py --env 172.118.57.100 --action get-ref --disk-name disk-name
python skill_disk_tools.py --env 172.118.57.100 --action get-detail --disk-name disk-name
python skill_disk_tools.py --env 172.118.57.100 --action list
python skill_node_tools.py --env 172.118.57.100 --action list
python skill_stor_tools.py --env 172.118.34.100 --action status
python skill_stack_tools.py --env 172.118.57.100 --action services
python skill_vm_tools.py --env 172.118.42.100 --template web --count 3
```

## ✅ 同步状态：
- ✅ 真正的skill目录已重命名
- ✅ 调用脚本已更新
- ✅ 功能完全对应
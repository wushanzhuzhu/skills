# MCP 功能演示

本演示展示了如何在 OpenCode 中使用 MCP (Model Context Protocol) 服务器来扩展 AI 助手的功能。

## 什么是 MCP？

MCP 是一个开放协议，允许 AI 助手连接到外部工具和服务。通过 MCP，你可以：

- 添加自定义工具到 OpenCode
- 连接到远程服务和 API
- 扩展 AI 助手的能力

## 演示内容

我们创建了一个简单的本地 MCP 服务器，提供以下工具：

1. **calculate** - 执行基本数学计算
2. **current_time** - 获取当前时间
3. **generate_uuid** - 生成唯一标识符

## 配置文件

`opencode.json` 配置了：
- 本地 MCP 服务器连接
- 工具启用/禁用设置
- 专用代理配置

## 使用示例

### 1. 数学计算
```
请帮我计算 15 * 8 + 32 的结果，使用 demo_server 工具
```

### 2. 获取时间
```
使用 demo_server 获取当前 ISO 格式的时间
```

### 3. 生成 UUID
```
请使用 demo_server 生成一个 UUID v4
```

### 4. 组合使用
```
使用 demo_server 工具帮我：
1. 计算圆的面积（半径为 5）
2. 获取当前时间戳
3. 生成一个项目 ID
```

## 运行演示

1. 安装依赖：
```bash
npm install
```

2. 启动 OpenCode 并加载配置

3. 在提示中使用示例命令测试 MCP 功能

## MCP 配置说明

### 本地服务器
```json
{
  "type": "local",
  "command": ["node", "/path/to/server.js"],
  "enabled": true
}
```

### 远程服务器
```json
{
  "type": "remote", 
  "url": "https://api.example.com/mcp",
  "headers": {
    "Authorization": "Bearer {env:API_KEY}"
  }
}
```

## 工具管理

- 全局启用/禁用：在 `tools` 配置中设置
- 按代理启用：在特定代理配置中启用
- 通配符支持：使用 `*` 模式匹配多个工具

## OAuth 支持

OpenCode 自动处理 OAuth 认证：
```bash
opencode mcp auth server-name
opencode mcp list
opencode mcp logout server-name
```
#!/usr/bin/env node

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ErrorCode,
  ListToolsRequestSchema,
  McpError,
} = require('@modelcontextprotocol/sdk/types.js');

class SimpleMCPServer {
  constructor() {
    this.server = new Server(
      {
        name: 'simple-demo-server',
        version: '0.1.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
  }

  setupToolHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'calculate',
            description: '执行基本的数学计算',
            inputSchema: {
              type: 'object',
              properties: {
                expression: {
                  type: 'string',
                  description: '要计算的数学表达式，如 "2 + 3" 或 "10 * 5"',
                },
              },
              required: ['expression'],
            },
          },
          {
            name: 'current_time',
            description: '获取当前时间',
            inputSchema: {
              type: 'object',
              properties: {
                format: {
                  type: 'string',
                  description: '时间格式，如 "iso", "unix", 或 "readable"',
                  enum: ['iso', 'unix', 'readable'],
                  default: 'readable',
                },
              },
            },
          },
          {
            name: 'generate_uuid',
            description: '生成一个随机的UUID',
            inputSchema: {
              type: 'object',
              properties: {
                version: {
                  type: 'string',
                  description: 'UUID版本',
                  enum: ['v4'],
                  default: 'v4',
                },
              },
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'calculate':
            return await this.handleCalculate(args);
          case 'current_time':
            return await this.handleCurrentTime(args);
          case 'generate_uuid':
            return await this.handleGenerateUUID(args);
          default:
            throw new McpError(
              ErrorCode.MethodNotFound,
              `Unknown tool: ${name}`
            );
        }
      } catch (error) {
        throw new McpError(
          ErrorCode.InternalError,
          `Tool execution failed: ${error.message}`
        );
      }
    });
  }

  async handleCalculate(args) {
    const { expression } = args;
    
    // 简单的数学表达式计算（仅支持基本运算）
    try {
      // 安全的数学表达式计算
      const sanitized = expression.replace(/[^0-9+\-*/().\s]/g, '');
      const result = Function('"use strict"; return (' + sanitized + ')')();
      
      return {
        content: [
          {
            type: 'text',
            text: `计算结果: ${expression} = ${result}`,
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `计算错误: 无法计算表达式 "${expression}"`,
          },
        ],
      };
    }
  }

  async handleCurrentTime(args) {
    const { format = 'readable' } = args;
    const now = new Date();
    
    let timeString;
    switch (format) {
      case 'iso':
        timeString = now.toISOString();
        break;
      case 'unix':
        timeString = Math.floor(now.getTime() / 1000).toString();
        break;
      case 'readable':
      default:
        timeString = now.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
        break;
    }

    return {
      content: [
        {
          type: 'text',
          text: `当前时间 (${format}): ${timeString}`,
        },
      ],
    };
  }

  async handleGenerateUUID(args) {
    const { version = 'v4' } = args;
    
    const uuid = this.generateUUID();
    
    return {
      content: [
        {
          type: 'text',
          text: `生成的UUID (${version}): ${uuid}`,
        },
      ],
    };
  }

  generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('Simple MCP Demo server running on stdio');
  }
}

const server = new SimpleMCPServer();
server.run().catch(console.error);
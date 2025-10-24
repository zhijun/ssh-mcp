#!/usr/bin/env python3
"""
SSH Agent MCP 服务使用示例
演示如何通过MCP协议与SSH Agent交互
"""
import asyncio
import json
import sys

async def example_usage():
    """演示MCP服务的基本用法"""
    print("=== SSH Agent MCP 服务使用示例 ===\n")
    
    print("1. 启动MCP服务:")
    print("   python main.py")
    print()
    
    print("2. 在大模型中可以使用以下工具:")
    print()
    
    print("建立SSH连接:")
    print(json.dumps({
        "name": "ssh_connect",
        "arguments": {
            "host": "192.168.1.100",
            "username": "admin",
            "password": "your_password"
        }
    }, indent=2))
    print()
    
    print("查询连接状态:")
    print(json.dumps({
        "name": "ssh_status",
        "arguments": {}
    }, indent=2))
    print()
    
    print("执行命令:")
    print(json.dumps({
        "name": "ssh_execute",
        "arguments": {
            "connection_id": "admin@192.168.1.100:22",
            "command": "ls -la"
        }
    }, indent=2))
    print()
    
    print("断开连接:")
    print(json.dumps({
        "name": "ssh_disconnect",
        "arguments": {
            "connection_id": "admin@192.168.1.100:22"
        }
    }, indent=2))
    print()
    
    print("=== 支持的认证方式 ===")
    print("1. 密码认证: 提供password参数")
    print("2. 私钥认证: 提供private_key参数（文件路径）")
    print("3. 私钥+密码: 提供private_key和private_key_password参数")
    print("4. SSH Agent: 不提供认证信息，自动使用本地SSH Agent")
    print()
    
    print("=== 安全建议 ===")
    print("1. 使用私钥认证而非密码认证")
    print("2. 定期轮换SSH密钥")
    print("3. 限制SSH用户权限")
    print("4. 监控SSH连接日志")

if __name__ == "__main__":
    asyncio.run(example_usage())
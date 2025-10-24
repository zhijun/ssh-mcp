#!/usr/bin/env python3
"""
测试MCP SSH Agent服务的脚本
"""
import asyncio
import json
import subprocess
import sys
import time
from typing import Dict, Any

class MCPTestClient:
    def __init__(self):
        self.process = None
        self.initialized = False
        
    async def start_server(self):
        """启动MCP服务器"""
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "main.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 初始化MCP会话
        await self.send_message({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        })
        
        # 等待初始化响应
        response = await self.read_message()
        if response and "result" in response:
            self.initialized = True
            print("✓ MCP服务器初始化成功")
            return True
        else:
            print("✗ MCP服务器初始化失败")
            return False
    
    async def send_message(self, message: Dict[str, Any]):
        """发送消息到MCP服务器"""
        if not self.process:
            return
            
        message_str = json.dumps(message) + "\n"
        self.process.stdin.write(message_str.encode())
        await self.process.stdin.drain()
    
    async def read_message(self) -> Dict[str, Any]:
        """从MCP服务器读取消息"""
        if not self.process:
            return None
            
        try:
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=5.0)
            if line:
                return json.loads(line.decode().strip())
        except asyncio.TimeoutError:
            print("读取消息超时")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
            
        return None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具"""
        if not self.initialized:
            return {"error": "MCP服务器未初始化"}
        
        message = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        await self.send_message(message)
        return await self.read_message()
    
    async def list_tools(self) -> Dict[str, Any]:
        """列出可用工具"""
        message = {
            "jsonrpc": "2.0",
            "id": int(time.time()),
            "method": "tools/list"
        }
        
        await self.send_message(message)
        return await self.read_message()
    
    async def stop(self):
        """停止MCP服务器"""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await self.process.wait()
            except ProcessLookupError:
                pass  # 进程已经结束

async def test_mcp_service():
    """测试MCP服务功能"""
    client = MCPTestClient()
    
    try:
        # 启动服务器
        if not await client.start_server():
            return False
        
        print("\n=== 测试MCP SSH Agent服务 ===\n")
        
        # 测试1: 列出可用工具
        print("1. 测试列出工具...")
        tools_response = await client.list_tools()
        if tools_response and "result" in tools_response:
            tools = tools_response["result"]["tools"]
            print(f"✓ 发现 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print("✗ 列出工具失败")
            return False
        
        # 测试2: 列出连接（应该为空）
        print("\n2. 测试列出连接...")
        connections_response = await client.call_tool("ssh_list_connections", {})
        if connections_response and "result" in connections_response:
            print("✓ 列出连接成功")
            print(connections_response["result"]["content"][0]["text"])
        else:
            print("✗ 列出连接失败")
        
        # 测试3: 尝试连接（使用虚拟参数，预期会失败）
        print("\n3. 测试SSH连接（预期失败）...")
        connect_response = await client.call_tool("ssh_connect", {
            "host": "127.0.0.1",
            "username": "test",
            "password": "test"
        })
        
        if connect_response:
            if "error" in connect_response:
                print("✓ 连接失败（符合预期）")
                print(f"错误信息: {connect_response['error']['message']}")
            else:
                print("✓ 连接测试完成")
                print(connect_response["result"]["content"][0]["text"])
        
        print("\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        return False
    finally:
        await client.stop()

if __name__ == "__main__":
    success = asyncio.run(test_mcp_service())
    sys.exit(0 if success else 1)
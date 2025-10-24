#!/usr/bin/env python3
"""
完整的MCP协议测试客户端
"""
import asyncio
import json
import sys
import subprocess
import time
from typing import Dict, Any

class MCPClient:
    def __init__(self):
        self.process = None
        self.request_id = 1
        
    async def start_server(self):
        """启动MCP服务器进程"""
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "main.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="/root/src/sshagent"
        )
        
        # 初始化MCP会话
        init_result = await self.send_request({
            "jsonrpc": "2.0",
            "id": self.request_id,
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
        
        self.request_id += 1
        return init_result is not None and "result" in init_result
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """发送请求并等待响应"""
        if not self.process:
            return None
            
        # 发送请求
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode())
        await self.process.stdin.drain()
        
        # 读取响应
        try:
            line = await asyncio.wait_for(self.process.stdout.readline(), timeout=10.0)
            if line:
                return json.loads(line.decode().strip())
        except asyncio.TimeoutError:
            print("请求超时")
            return None
        except json.JSONDecodeError as e:
            print(f"JSON解析错误: {e}")
            return None
            
        return None
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用MCP工具"""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        self.request_id += 1
        return await self.send_request(request)
    
    async def list_tools(self) -> Dict[str, Any]:
        """列出可用工具"""
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": "tools/list"
        }
        
        self.request_id += 1
        return await self.send_request(request)
    
    async def stop(self):
        """停止MCP服务器"""
        if self.process and self.process.returncode is None:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()

async def test_mcp_complete():
    """完整的MCP协议测试"""
    print("=== 完整MCP协议测试 ===\n")
    
    client = MCPClient()
    
    try:
        # 启动服务器
        print("1. 启动MCP服务器...")
        if not await client.start_server():
            print("✗ 启动失败")
            return False
        print("✓ MCP服务器启动成功")
        
        # 列出工具
        print("\n2. 列出可用工具...")
        tools_response = await client.list_tools()
        if tools_response and "result" in tools_response:
            tools = tools_response["result"]["tools"]
            print(f"✓ 发现 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print("✗ 列出工具失败")
            return False
        
        # 列出连接
        print("\n3. 列出当前连接...")
        connections_response = await client.call_tool("ssh_list_connections", {})
        if connections_response and "result" in connections_response:
            print("✓ 列出连接成功:")
            print(connections_response["result"]["content"][0]["text"])
        else:
            print("✗ 列出连接失败")
        
        # 建立SSH连接
        print("\n4. 建立SSH连接...")
        connect_response = await client.call_tool("ssh_connect", {
            "host": "127.0.0.1",
            "username": "root",
            "private_key": "/root/.ssh/test_key"
        })
        
        if connect_response and "result" in connect_response:
            print("✓ SSH连接成功:")
            print(connect_response["result"]["content"][0]["text"])
            connection_id = "root@127.0.0.1:22"
        else:
            print("✗ SSH连接失败")
            if connect_response and "error" in connect_response:
                print(f"错误: {connect_response['error']['message']}")
            return False
        
        # 查询连接状态
        print("\n5. 查询连接状态...")
        status_response = await client.call_tool("ssh_status", {})
        if status_response and "result" in status_response:
            print("✓ 查询状态成功:")
            print(status_response["result"]["content"][0]["text"])
        
        # 执行命令
        print("\n6. 执行命令...")
        commands = [
            "whoami",
            "pwd",
            "ls -la",
            "uname -a"
        ]
        
        for cmd in commands:
            print(f"\n执行命令: {cmd}")
            exec_response = await client.call_tool("ssh_execute", {
                "connection_id": connection_id,
                "command": cmd
            })
            
            if exec_response and "result" in exec_response:
                result = exec_response["result"]["content"][0]["text"]
                print("✓ 命令执行成功")
                # 只显示输出的前几行
                lines = result.split('\n')
                for line in lines[:10]:
                    print(f"  {line}")
                if len(lines) > 10:
                    print(f"  ... (还有 {len(lines) - 10} 行)")
            else:
                print("✗ 命令执行失败")
        
        # 断开连接
        print("\n7. 断开SSH连接...")
        disconnect_response = await client.call_tool("ssh_disconnect", {
            "connection_id": connection_id
        })
        
        if disconnect_response and "result" in disconnect_response:
            print("✓ 断开连接成功:")
            print(disconnect_response["result"]["content"][0]["text"])
        
        print("\n=== 测试完成 ===")
        return True
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        return False
    finally:
        await client.stop()

if __name__ == "__main__":
    success = asyncio.run(test_mcp_complete())
    sys.exit(0 if success else 1)
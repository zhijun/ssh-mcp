#!/usr/bin/env python3
"""
MCP交互式工具测试脚本

此脚本直接测试MCP服务器的交互式工具功能，
模拟MCP客户端的调用方式。

使用方法:
1. 修改连接参数
2. 运行脚本: python test_mcp_interactive.py
"""

import asyncio
import json
from mcp_server import handle_call_tool, ssh_manager
from mcp.types import CallToolResult

async def test_mcp_interactive_tools():
    """测试MCP交互式工具"""
    
    print("=== MCP 交互式工具测试 ===\n")
    
    # 连接参数 - 请根据实际情况修改
    connection_params = {
        "host": "localhost",  # 修改为你的SSH服务器
        "username": "testuser",  # 修改为你的用户名
        "port": 22,
        "password": "testpass"  # 或使用私钥认证
    }
    
    try:
        # 1. 建立SSH连接
        print("1. 建立SSH连接...")
        result = await handle_call_tool("ssh_connect", connection_params)
        print(f"   结果: {result.content[0].text}")
        
        if result.isError:
            print("   连接失败，跳过后续测试")
            return
        
        # 从结果中提取连接ID
        connection_id = None
        for line in result.content[0].text.split('\n'):
            if line.startswith('连接ID:'):
                connection_id = line.split(':')[1].strip()
                break
        
        if not connection_id:
            print("   无法获取连接ID")
            return
        
        print(f"   连接ID: {connection_id}\n")
        
        # 2. 启动交互式会话
        print("2. 启动交互式bash会话...")
        result = await handle_call_tool("ssh_start_interactive", {
            "connection_id": connection_id,
            "command": "bash",
            "pty_width": 80,
            "pty_height": 24
        })
        print(f"   结果: {result.content[0].text}")
        
        if result.isError:
            print("   启动交互式会话失败")
            return
        
        # 从结果中提取会话ID
        session_id = None
        for line in result.content[0].text.split('\n'):
            if line.startswith('会话ID:'):
                session_id = line.split(':')[1].strip()
                break
        
        if not session_id:
            print("   无法获取会话ID")
            return
        
        print(f"   会话ID: {session_id}\n")
        
        # 等待会话启动
        await asyncio.sleep(2)
        
        # 3. 获取初始输出
        print("3. 获取初始输出...")
        result = await handle_call_tool("ssh_get_interactive_output", {
            "session_id": session_id,
            "max_lines": 10
        })
        print(f"   结果:\n{result.content[0].text}\n")
        
        # 4. 发送命令并获取输出
        commands = [
            "echo 'Hello Interactive MCP!'",
            "pwd",
            "date",
            "whoami"
        ]
        
        for i, cmd in enumerate(commands, 1):
            print(f"4.{i} 发送命令: {cmd}")
            
            # 发送命令
            result = await handle_call_tool("ssh_send_input", {
                "session_id": session_id,
                "input_text": cmd + "\n"
            })
            print(f"     发送结果: {result.content[0].text}")
            
            # 等待命令执行
            await asyncio.sleep(1)
            
            # 获取输出
            result = await handle_call_tool("ssh_get_interactive_output", {
                "session_id": session_id,
                "max_lines": 20
            })
            print(f"     输出:\n{result.content[0].text}\n")
        
        # 5. 列出所有交互式会话
        print("5. 列出所有交互式会话...")
        result = await handle_call_tool("ssh_list_interactive_sessions", {})
        print(f"   结果:\n{result.content[0].text}\n")
        
        # 6. 测试Python交互式环境
        print("6. 启动Python交互式会话...")
        result = await handle_call_tool("ssh_start_interactive", {
            "connection_id": connection_id,
            "command": "python3",
            "pty_width": 80,
            "pty_height": 24
        })
        print(f"   结果: {result.content[0].text}")
        
        if not result.isError:
            # 从结果中提取Python会话ID
            python_session_id = None
            for line in result.content[0].text.split('\n'):
                if line.startswith('会话ID:'):
                    python_session_id = line.split(':')[1].strip()
                    break
            
            if python_session_id:
                print(f"   Python会话ID: {python_session_id}")
                
                # 等待Python启动
                await asyncio.sleep(2)
                
                # 获取Python提示符
                result = await handle_call_tool("ssh_get_interactive_output", {
                    "session_id": python_session_id,
                    "max_lines": 10
                })
                print(f"   Python启动输出:\n{result.content[0].text}")
                
                # 发送Python命令
                python_commands = [
                    "print('Hello from Python via MCP!')",
                    "import sys",
                    "print(f'Python version: {sys.version}')",
                    "exit()"
                ]
                
                for cmd in python_commands:
                    print(f"\n   发送Python命令: {cmd}")
                    
                    # 发送命令
                    await handle_call_tool("ssh_send_input", {
                        "session_id": python_session_id,
                        "input_text": cmd + "\n"
                    })
                    
                    # 等待执行
                    await asyncio.sleep(1)
                    
                    # 获取输出
                    result = await handle_call_tool("ssh_get_interactive_output", {
                        "session_id": python_session_id,
                        "max_lines": 10
                    })
                    print(f"   输出:\n{result.content[0].text}")
                
                print("   Python会话已自动退出\n")
        
        # 7. 终止bash会话
        print("7. 终止bash会话...")
        result = await handle_call_tool("ssh_terminate_interactive", {
            "session_id": session_id
        })
        print(f"   结果: {result.content[0].text}\n")
        
        # 8. 再次列出会话（应该为空或更少）
        print("8. 再次列出交互式会话...")
        result = await handle_call_tool("ssh_list_interactive_sessions", {})
        print(f"   结果:\n{result.content[0].text}\n")
        
        # 9. 断开SSH连接
        print("9. 断开SSH连接...")
        result = await handle_call_tool("ssh_disconnect", {
            "connection_id": connection_id
        })
        print(f"   结果: {result.content[0].text}")
        
        print("\n=== MCP交互式工具测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("\n清理资源...")
        await ssh_manager.disconnect_all()
        await ssh_manager.shutdown()

async def test_sudo_workflow():
    """测试sudo工作流程"""
    
    print("\n=== Sudo工作流程测试 ===")
    
    # 连接参数
    connection_params = {
        "host": "localhost",
        "username": "testuser",
        "port": 22,
        "password": "testpass"
    }
    
    try:
        # 建立连接
        print("1. 建立SSH连接...")
        result = await handle_call_tool("ssh_connect", connection_params)
        
        if result.isError:
            print(f"   连接失败: {result.content[0].text}")
            return
        
        # 提取连接ID
        connection_id = None
        for line in result.content[0].text.split('\n'):
            if line.startswith('连接ID:'):
                connection_id = line.split(':')[1].strip()
                break
        
        if not connection_id:
            print("   无法获取连接ID")
            return
        
        print(f"   连接成功，ID: {connection_id}")
        
        # 启动sudo命令
        print("\n2. 启动sudo命令...")
        result = await handle_call_tool("ssh_start_interactive", {
            "connection_id": connection_id,
            "command": "sudo whoami",
            "pty_width": 80,
            "pty_height": 24
        })
        
        if result.isError:
            print(f"   启动sudo失败: {result.content[0].text}")
            return
        
        # 提取会话ID
        session_id = None
        for line in result.content[0].text.split('\n'):
            if line.startswith('会话ID:'):
                session_id = line.split(':')[1].strip()
                break
        
        print(f"   Sudo会话启动，ID: {session_id}")
        
        # 等待密码提示
        await asyncio.sleep(2)
        
        # 获取输出，检查是否有密码提示
        print("\n3. 检查密码提示...")
        result = await handle_call_tool("ssh_get_interactive_output", {
            "session_id": session_id,
            "max_lines": 10
        })
        
        output_text = result.content[0].text
        print(f"   输出:\n{output_text}")
        
        # 检查是否需要密码
        if "password" in output_text.lower() or "密码" in output_text:
            print("\n4. 检测到密码提示，发送密码...")
            result = await handle_call_tool("ssh_send_input", {
                "session_id": session_id,
                "input_text": "testpass\n"  # 注意：实际使用中应安全处理密码
            })
            print(f"   密码发送结果: {result.content[0].text}")
            
            # 等待sudo执行
            await asyncio.sleep(2)
            
            # 获取sudo执行结果
            print("\n5. 获取sudo执行结果...")
            result = await handle_call_tool("ssh_get_interactive_output", {
                "session_id": session_id,
                "max_lines": 10
            })
            print(f"   Sudo执行结果:\n{result.content[0].text}")
        else:
            print("   未检测到密码提示，可能已有sudo权限或配置了无密码sudo")
        
        # 终止会话
        print("\n6. 终止sudo会话...")
        result = await handle_call_tool("ssh_terminate_interactive", {
            "session_id": session_id
        })
        print(f"   结果: {result.content[0].text}")
        
        # 断开连接
        await handle_call_tool("ssh_disconnect", {"connection_id": connection_id})
        
        print("\n=== Sudo工作流程测试完成 ===")
        
    except Exception as e:
        print(f"Sudo测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("MCP 交互式工具测试")
    print("=" * 50)
    print("注意：请在运行前修改连接参数！")
    print("=" * 50)
    
    # 运行基本MCP工具测试
    asyncio.run(test_mcp_interactive_tools())
    
    # 运行sudo工作流程测试
    asyncio.run(test_sudo_workflow())
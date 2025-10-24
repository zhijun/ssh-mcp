#!/usr/bin/env python3
"""
交互式SSH命令测试脚本

此脚本演示如何使用SSH MCP的交互式功能来处理需要用户输入的命令，
如sudo、vim、mysql等。

使用方法:
1. 确保SSH MCP服务正在运行
2. 修改下面的连接参数
3. 运行脚本: python test_interactive.py
"""

import asyncio
import json
import time
from ssh_manager import SSHManager

async def test_interactive_commands():
    """测试交互式命令功能"""
    
    # 创建SSH管理器
    ssh_manager = SSHManager()
    
    # 连接参数 - 请根据实际情况修改
    connection_params = {
        "host": "localhost",  # 修改为你的SSH服务器
        "username": "testuser",  # 修改为你的用户名
        "port": 22,
        "password": "testpass"  # 或使用私钥认证
    }
    
    try:
        print("=== SSH MCP 交互式命令测试 ===\n")
        
        # 1. 建立SSH连接
        print("1. 建立SSH连接...")
        connection_id = await ssh_manager.create_connection(**connection_params)
        print(f"   连接ID: {connection_id}")
        
        # 检查连接状态
        status = await ssh_manager.get_connection_status(connection_id)
        if status["status"] != "connected":
            print(f"   连接失败: {status.get('error_message', '未知错误')}")
            return
        print("   连接成功!\n")
        
        # 2. 测试基本交互式命令 - bash shell
        print("2. 测试基本交互式命令 (bash)...")
        session_id = await ssh_manager.start_interactive_session(
            connection_id=connection_id,
            command="bash",
            pty_width=80,
            pty_height=24
        )
        print(f"   会话ID: {session_id}")
        
        # 等待一下让shell启动
        await asyncio.sleep(1)
        
        # 获取初始输出
        output = await ssh_manager.get_interactive_output(session_id)
        if output and output['output']:
            print("   初始输出:")
            for line in output['output'][-5:]:  # 显示最后5行
                print(f"     {line}")
        
        # 发送一些命令
        commands = ["echo 'Hello Interactive SSH!'", "pwd", "ls -la"]
        for cmd in commands:
            print(f"\n   发送命令: {cmd}")
            await ssh_manager.send_input_to_session(session_id, cmd + "\n")
            await asyncio.sleep(1)  # 等待命令执行
            
            # 获取输出
            output = await ssh_manager.get_interactive_output(session_id)
            if output and output['output']:
                print("   输出:")
                for line in output['output'][-10:]:  # 显示最后10行
                    print(f"     {line}")
        
        # 终止会话
        await ssh_manager.terminate_interactive_session(session_id)
        print("   bash会话已终止\n")
        
        # 3. 测试sudo命令 (如果有sudo权限)
        print("3. 测试sudo命令...")
        try:
            session_id = await ssh_manager.start_interactive_session(
                connection_id=connection_id,
                command="sudo whoami",
                pty_width=80,
                pty_height=24
            )
            print(f"   会话ID: {session_id}")
            
            await asyncio.sleep(1)
            
            # 获取输出，可能包含密码提示
            output = await ssh_manager.get_interactive_output(session_id)
            if output and output['output']:
                print("   输出:")
                for line in output['output']:
                    print(f"     {line}")
                    if "password" in line.lower() or "密码" in line:
                        print("   检测到密码提示，发送密码...")
                        # 注意：在实际使用中，密码应该安全地获取
                        await ssh_manager.send_input_to_session(session_id, "testpass\n")
                        await asyncio.sleep(2)
                        
                        # 获取sudo执行结果
                        output = await ssh_manager.get_interactive_output(session_id)
                        if output and output['output']:
                            print("   sudo执行结果:")
                            for line in output['output'][-5:]:
                                print(f"     {line}")
            
            await ssh_manager.terminate_interactive_session(session_id)
            print("   sudo会话已终止\n")
            
        except Exception as e:
            print(f"   sudo测试失败: {e}\n")
        
        # 4. 测试Python交互式环境
        print("4. 测试Python交互式环境...")
        try:
            session_id = await ssh_manager.start_interactive_session(
                connection_id=connection_id,
                command="python3",
                pty_width=80,
                pty_height=24
            )
            print(f"   会话ID: {session_id}")
            
            await asyncio.sleep(1)
            
            # 获取Python提示符
            output = await ssh_manager.get_interactive_output(session_id)
            if output and output['output']:
                print("   Python启动输出:")
                for line in output['output']:
                    print(f"     {line}")
            
            # 发送Python命令
            python_commands = [
                "print('Hello from Python!')",
                "import os",
                "print(f'Current directory: {os.getcwd()}')",
                "exit()"
            ]
            
            for cmd in python_commands:
                print(f"\n   发送Python命令: {cmd}")
                await ssh_manager.send_input_to_session(session_id, cmd + "\n")
                await asyncio.sleep(1)
                
                # 获取输出
                output = await ssh_manager.get_interactive_output(session_id)
                if output and output['output']:
                    print("   输出:")
                    for line in output['output'][-5:]:
                        print(f"     {line}")
            
            await ssh_manager.terminate_interactive_session(session_id)
            print("   Python会话已终止\n")
            
        except Exception as e:
            print(f"   Python测试失败: {e}\n")
        
        # 5. 列出所有活跃会话
        print("5. 列出所有活跃会话...")
        sessions = await ssh_manager.list_interactive_sessions()
        if sessions:
            print(f"   活跃会话数: {len(sessions)}")
            for sid, info in sessions.items():
                print(f"   会话 {sid}: {info['command']} (状态: {info['status']})")
        else:
            print("   没有活跃的交互式会话")
        
        print("\n=== 测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("\n清理资源...")
        await ssh_manager.disconnect_all()
        await ssh_manager.shutdown()

async def test_interactive_workflow():
    """演示完整的交互式工作流程"""
    
    print("\n=== 交互式工作流程演示 ===")
    print("此演示展示如何使用交互式功能进行复杂的操作")
    
    ssh_manager = SSHManager()
    
    # 连接参数
    connection_params = {
        "host": "localhost",
        "username": "testuser",
        "port": 22,
        "password": "testpass"
    }
    
    try:
        # 建立连接
        connection_id = await ssh_manager.create_connection(**connection_params)
        status = await ssh_manager.get_connection_status(connection_id)
        
        if status["status"] != "connected":
            print(f"连接失败: {status.get('error_message')}")
            return
        
        print("连接成功，开始演示工作流程...\n")
        
        # 工作流程：创建文件 -> 编辑 -> 查看 -> 删除
        print("1. 启动bash会话...")
        session_id = await ssh_manager.start_interactive_session(
            connection_id=connection_id,
            command="bash"
        )
        
        await asyncio.sleep(1)
        
        # 创建测试文件
        print("2. 创建测试文件...")
        await ssh_manager.send_input_to_session(session_id, "echo 'Hello World' > test_file.txt\n")
        await asyncio.sleep(1)
        
        # 查看文件内容
        print("3. 查看文件内容...")
        await ssh_manager.send_input_to_session(session_id, "cat test_file.txt\n")
        await asyncio.sleep(1)
        
        # 获取输出
        output = await ssh_manager.get_interactive_output(session_id)
        if output and output['output']:
            print("   输出:")
            for line in output['output'][-10:]:
                print(f"     {line}")
        
        # 使用sed编辑文件
        print("4. 使用sed编辑文件...")
        await ssh_manager.send_input_to_session(session_id, "sed -i 's/World/Interactive SSH/' test_file.txt\n")
        await asyncio.sleep(1)
        
        # 再次查看文件
        print("5. 查看编辑后的文件...")
        await ssh_manager.send_input_to_session(session_id, "cat test_file.txt\n")
        await asyncio.sleep(1)
        
        # 获取最终输出
        output = await ssh_manager.get_interactive_output(session_id)
        if output and output['output']:
            print("   最终输出:")
            for line in output['output'][-10:]:
                print(f"     {line}")
        
        # 清理测试文件
        print("6. 清理测试文件...")
        await ssh_manager.send_input_to_session(session_id, "rm test_file.txt\n")
        await asyncio.sleep(1)
        
        # 终止会话
        await ssh_manager.terminate_interactive_session(session_id)
        print("工作流程演示完成！\n")
        
    except Exception as e:
        print(f"工作流程演示失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await ssh_manager.disconnect_all()
        await ssh_manager.shutdown()

if __name__ == "__main__":
    print("SSH MCP 交互式命令测试")
    print("=" * 50)
    print("注意：请在运行前修改连接参数！")
    print("=" * 50)
    
    # 运行基本测试
    asyncio.run(test_interactive_commands())
    
    # 运行工作流程演示
    asyncio.run(test_interactive_workflow())
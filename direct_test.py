#!/usr/bin/env python3
"""
直接测试MCP SSH服务的客户端
"""
import asyncio
import json
import sys
import os

# 添加项目路径
sys.path.insert(0, '/root/src/sshagent')

from ssh_manager import SSHManager

async def test_ssh_functionality():
    """直接测试SSH管理器功能"""
    print("=== 直接测试SSH管理器功能 ===\n")
    
    manager = SSHManager()
    
    # 测试1: 列出空连接
    print("1. 列出当前连接（应该为空）:")
    connections = await manager.list_connections()
    print(json.dumps(connections, indent=2, ensure_ascii=False))
    print()
    
    # 测试2: 尝试连接到本地SSH服务（如果存在）
    print("2. 尝试连接本地SSH服务:")
    try:
        # 首先检查本地是否有SSH服务运行
        import subprocess
        result = subprocess.run(['netstat', '-tlnp'], capture_output=True, text=True)
        if ':22 ' in result.stdout:
            print("检测到本地SSH服务运行中，尝试连接...")
            connection_id = await manager.create_connection(
                host="127.0.0.1",
                username="root",
                port=22,
                private_key="/root/.ssh/test_key"
            )
            print(f"连接成功! 连接ID: {connection_id}")
            
            # 测试3: 执行简单命令
            print("\n3. 执行命令 'whoami':")
            result = await manager.execute_command(connection_id, "whoami")
            print(f"成功: {result['success']}")
            print(f"退出码: {result['exit_code']}")
            print(f"输出: {result['stdout'].strip()}")
            if result['stderr']:
                print(f"错误: {result['stderr']}")
            
            # 测试4: 查询连接状态
            print("\n4. 查询连接状态:")
            status = await manager.get_connection_status(connection_id)
            print(json.dumps(status, indent=2, ensure_ascii=False))
            
            # 测试5: 断开连接
            print("\n5. 断开连接:")
            success = await manager.disconnect(connection_id)
            print(f"断开成功: {success}")
            
        else:
            print("本地没有检测到SSH服务运行在端口22")
            # 测试连接一个不存在的地址
            print("尝试连接不存在的地址（预期失败）:")
            try:
                await manager.create_connection(
                    host="192.168.255.254",
                    username="test",
                    password="test"
                )
            except Exception as e:
                print(f"连接失败（符合预期）: {e}")
                
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
    
    # 测试6: 再次列出连接（应该为空）
    print("\n6. 最终连接列表:")
    connections = await manager.list_connections()
    print(json.dumps(connections, indent=2, ensure_ascii=False))
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_ssh_functionality())

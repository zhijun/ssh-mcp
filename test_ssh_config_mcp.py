#!/usr/bin/env python3
"""
测试SSH config MCP工具功能
"""
import asyncio
import json
import sys
import os
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp_server import handle_call_tool

async def test_mcp_ssh_config_tools():
    """测试MCP SSH config工具"""
    print("开始测试MCP SSH config工具...")
    
    # 设置SSH config文件
    ssh_config_path = Path.home() / '.ssh' / 'config'
    backup_ssh_config = None
    
    try:
        # 备份原始SSH config文件
        if ssh_config_path.exists():
            backup_ssh_config = ssh_config_path.with_suffix('.config.backup.mcp')
            shutil.copy2(ssh_config_path, backup_ssh_config)
            print(f"已备份原始SSH config到: {backup_ssh_config}")
        
        # 确保.ssh目录存在
        ssh_dir = Path.home() / '.ssh'
        ssh_dir.mkdir(exist_ok=True)
        
        # 复制测试配置文件到SSH config位置
        test_config_path = project_root / 'test_ssh_config'
        shutil.copy2(test_config_path, ssh_config_path)
        print(f"已设置测试SSH config文件: {ssh_config_path}")
        
        # 等待一下确保文件系统操作完成
        await asyncio.sleep(0.1)
        # 测试1: ssh_connect_by_config_host工具
        print("\n=== 测试1: ssh_connect_by_config_host工具 ===")
        
        # 测试有效配置
        result = await handle_call_tool("ssh_connect_by_config_host", {
            "config_host": "test-local"
        })
        
        print("工具调用结果:")
        print(f"是否错误: {result.isError}")
        for content in result.content:
            if hasattr(content, 'text'):
                print(f"输出: {content.text}")
        
        # 测试参数覆盖
        print("\n--- 测试参数覆盖 ---")
        result = await handle_call_tool("ssh_connect_by_config_host", {
            "config_host": "test-password",
            "username": "override_user",
            "password": "test_password"
        })
        
        print("参数覆盖结果:")
        print(f"是否错误: {result.isError}")
        for content in result.content:
            if hasattr(content, 'text'):
                print(f"输出: {content.text}")
        
        # 测试不存在的配置
        print("\n--- 测试不存在的配置 ---")
        result = await handle_call_tool("ssh_connect_by_config_host", {
            "config_host": "non-existent-host"
        })
        
        print("不存在配置结果:")
        print(f"是否错误: {result.isError}")
        for content in result.content:
            if hasattr(content, 'text'):
                print(f"输出: {content.text}")
        
        # 测试2: 查看连接状态
        print("\n=== 测试2: 查看连接状态 ===")
        result = await handle_call_tool("ssh_list_connections", {})
        
        print("连接列表:")
        for content in result.content:
            if hasattr(content, 'text'):
                print(content.text)
        
        # 测试3: 执行命令（如果连接成功）
        print("\n=== 测试3: 执行命令测试 ===")
        result = await handle_call_tool("ssh_status", {})
        
        # 查找成功的连接
        successful_connection = None
        for content in result.content:
            if hasattr(content, 'text'):
                # 简单解析输出查找成功连接
                if "connected" in content.text:
                    lines = content.text.split('\n')
                    for line in lines:
                        if "connected" in line and "connection_id" in line:
                            # 尝试提取连接ID
                            import re
                            match = re.search(r'(\S+@\S+:\d+)', line)
                            if match:
                                successful_connection = match.group(1)
                                break
        
        if successful_connection:
            print(f"找到成功连接: {successful_connection}")
            result = await handle_call_tool("ssh_execute", {
                "connection_id": successful_connection,
                "command": "echo 'SSH config connection test successful!'",
                "timeout": 10
            })
            
            print("命令执行结果:")
            print(f"是否错误: {result.isError}")
            for content in result.content:
                if hasattr(content, 'text'):
                    print(content.text)
        else:
            print("没有找到成功的连接，跳过命令执行测试")
        
        # 测试4: 断开所有连接
        print("\n=== 测试4: 断开所有连接 ===")
        result = await handle_call_tool("ssh_disconnect_all", {})
        
        print("断开连接结果:")
        for content in result.content:
            if hasattr(content, 'text'):
                print(content.text)
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 恢复原始SSH config文件
        try:
            if backup_ssh_config and backup_ssh_config.exists():
                shutil.copy2(backup_ssh_config, ssh_config_path)
                backup_ssh_config.unlink()
                print(f"\n已恢复原始SSH config文件")
            elif ssh_config_path.exists():
                ssh_config_path.unlink()
                print(f"\n已删除测试SSH config文件")
        except Exception as e:
            print(f"恢复SSH config文件时出错: {e}")
    
    print("\nMCP工具测试完成!")

if __name__ == "__main__":
    asyncio.run(test_mcp_ssh_config_tools())
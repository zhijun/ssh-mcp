#!/usr/bin/env python3
"""
测试SSH config连接功能
"""
import asyncio
import os
import sys
import tempfile
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ssh_manager import SSHManager

async def test_ssh_config_connection():
    """测试SSH config连接功能"""
    print("开始测试SSH config连接功能...")
    
    # 创建临时SSH config文件
    original_ssh_config = None
    temp_ssh_config = None
    backup_ssh_config = None
    
    try:
        # 备份原始SSH config文件
        ssh_config_path = Path.home() / '.ssh' / 'config'
        if ssh_config_path.exists():
            backup_ssh_config = ssh_config_path.with_suffix('.config.backup')
            shutil.copy2(ssh_config_path, backup_ssh_config)
            print(f"已备份原始SSH config到: {backup_ssh_config}")
        
        # 确保.ssh目录存在
        ssh_dir = Path.home() / '.ssh'
        ssh_dir.mkdir(exist_ok=True)
        
        # 复制测试配置文件到SSH config位置
        test_config_path = project_root / 'test_ssh_config'
        shutil.copy2(test_config_path, ssh_config_path)
        print(f"已设置测试SSH config文件: {ssh_config_path}")
        
        # 创建SSH Manager
        ssh_manager = SSHManager()
        
        # 测试1: 测试配置文件加载
        print("\n=== 测试1: SSH config文件解析 ===")
        import paramiko
        ssh_config = paramiko.SSHConfig()
        with open(ssh_config_path, 'r') as f:
            ssh_config.parse(f)
        
        # 测试解析各个主机配置
        test_hosts = ['test-local', 'test-password', 'test-custom-port', 'test-with-options']
        for host in test_hosts:
            config = ssh_config.lookup(host)
            print(f"主机 '{host}' 配置:")
            print(f"  HostName: {config.get('hostname', 'N/A')}")
            print(f"  User: {config.get('user', 'N/A')}")
            print(f"  Port: {config.get('port', 'N/A')}")
            print(f"  IdentityFile: {config.get('identityfile', 'N/A')}")
        
        # 测试2: 测试连接创建（不实际连接）
        print("\n=== 测试2: 连接对象创建 ===")
        
        # 测试使用config_host创建连接
        for host in test_hosts:
            try:
                connection_id = await ssh_manager.create_connection_from_config(
                    config_host=host
                )
                print(f"✓ 成功创建连接对象: {connection_id}")
                
                # 检查连接状态
                status = await ssh_manager.get_connection_status(connection_id)
                print(f"  状态: {status['status']}")
                if status.get('error_message'):
                    print(f"  错误: {status['error_message']}")
                
            except Exception as e:
                print(f"✗ 创建连接失败 '{host}': {e}")
        
        # 测试3: 测试参数覆盖
        print("\n=== 测试3: 参数覆盖测试 ===")
        try:
            connection_id = await ssh_manager.create_connection_from_config(
                config_host='test-password',
                username='override_user',
                password='test_password'
            )
            print(f"✓ 成功创建带参数覆盖的连接: {connection_id}")
            
            status = await ssh_manager.get_connection_status(connection_id)
            print(f"  状态: {status['status']}")
            
        except Exception as e:
            print(f"✗ 参数覆盖测试失败: {e}")
        
        # 测试4: 测试不存在的配置
        print("\n=== 测试4: 不存在配置测试 ===")
        try:
            connection_id = await ssh_manager.create_connection_from_config(
                config_host='non-existent-host'
            )
            print(f"✓ 处理不存在配置: {connection_id}")
            
            status = await ssh_manager.get_connection_status(connection_id)
            print(f"  状态: {status['status']}")
            if status.get('error_message'):
                print(f"  错误: {status['error_message']}")
                
        except Exception as e:
            print(f"✗ 不存在配置测试失败: {e}")
        
        # 列出所有连接
        print("\n=== 所有连接状态 ===")
        connections = await ssh_manager.list_connections()
        for conn_id, conn_info in connections.items():
            print(f"连接 {conn_id}:")
            print(f"  状态: {conn_info['status']}")
            print(f"  主机: {conn_info['host']}:{conn_info['port']}")
            print(f"  用户: {conn_info['username']}")
            if conn_info.get('error_message'):
                print(f"  错误: {conn_info['error_message']}")
        
        # 清理连接
        await ssh_manager.disconnect_all()
        
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
    
    print("\n测试完成!")

if __name__ == "__main__":
    asyncio.run(test_ssh_config_connection())
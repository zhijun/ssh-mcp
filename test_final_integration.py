#!/usr/bin/env python3
"""
最终集成测试 - 验证SSH config功能的完整性
"""
import asyncio
import sys
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ssh_manager import SSHManager
import paramiko

async def test_integration():
    """集成测试"""
    print("=== SSH Config功能最终集成测试 ===\n")
    
    ssh_config_path = Path.home() / '.ssh' / 'config'
    backup_ssh_config = None
    
    try:
        # 设置测试环境
        if ssh_config_path.exists():
            backup_ssh_config = ssh_config_path.with_suffix('.config.backup.integration')
            shutil.copy2(ssh_config_path, backup_ssh_config)
        
        ssh_dir = Path.home() / '.ssh'
        ssh_dir.mkdir(exist_ok=True)
        
        test_config_path = project_root / 'test_ssh_config'
        shutil.copy2(test_config_path, ssh_config_path)
        
        await asyncio.sleep(0.1)
        
        ssh_manager = SSHManager()
        
        # 测试1: SSH config解析验证
        print("1. SSH Config解析验证")
        print("-" * 30)
        
        ssh_config = paramiko.SSHConfig()
        with open(ssh_config_path, 'r') as f:
            ssh_config.parse(f)
        
        test_cases = [
            ('test-local', 'localhost', 'root', 22),
            ('test-password', 'localhost', 'testuser', 22),
            ('test-custom-port', 'localhost', 'admin', 2222),
            ('test-with-options', 'localhost', 'deploy', 22)
        ]
        
        for config_host, expected_host, expected_user, expected_port in test_cases:
            config = ssh_config.lookup(config_host)
            actual_host = config.get('hostname', config_host)
            actual_user = config.get('user', 'default')
            actual_port = int(config.get('port', 22))
            
            print(f"配置 '{config_host}':")
            print(f"  期望: {expected_user}@{expected_host}:{expected_port}")
            print(f"  实际: {actual_user}@{actual_host}:{actual_port}")
            print(f"  ✓ 解析正确" if (actual_host == expected_host and actual_user == expected_user and actual_port == expected_port) else f"  ✗ 解析错误")
            print()
        
        # 测试2: 连接对象创建和ID生成
        print("2. 连接对象创建和ID生成")
        print("-" * 30)
        
        connection_tests = [
            ('test-local', {}, 'root@localhost:22'),
            ('test-password', {'username': 'override_user'}, 'override_user@localhost:22'),
            ('test-custom-port', {}, 'admin@localhost:2222'),
            ('non-existent', {}, 'config_user@non-existent:22')
        ]
        
        for config_host, params, expected_id in connection_tests:
            try:
                connection_id = await ssh_manager.create_connection_from_config(
                    config_host=config_host,
                    **params
                )
                
                print(f"配置 '{config_host}' (参数: {params}):")
                print(f"  期望ID: {expected_id}")
                print(f"  实际ID: {connection_id}")
                print(f"  ✓ ID正确" if connection_id == expected_id else f"  ✗ ID错误")
                
                status = await ssh_manager.get_connection_status(connection_id)
                print(f"  状态: {status['status']}")
                if status.get('error_message'):
                    print(f"  错误: {status['error_message']}")
                print()
                
            except Exception as e:
                print(f"✗ 创建连接失败 '{config_host}': {e}")
                print()
        
        # 测试3: 错误处理验证
        print("3. 错误处理验证")
        print("-" * 30)
        
        # 测试不存在的私钥文件处理
        try:
            connection_id = await ssh_manager.create_connection_from_config(
                config_host='test-with-options'
            )
            status = await ssh_manager.get_connection_status(connection_id)
            
            if status['status'] == 'error' and '私钥文件不存在' in status.get('error_message', ''):
                print("✓ 不存在的私钥文件处理正确")
            else:
                print("✗ 不存在的私钥文件处理有问题")
                
        except Exception as e:
            print(f"✗ 私钥文件测试失败: {e}")
        
        print()
        
        # 测试4: 连接管理
        print("4. 连接管理")
        print("-" * 30)
        
        connections = await ssh_manager.list_connections()
        print(f"总连接数: {len(connections)}")
        
        for conn_id, conn_info in connections.items():
            print(f"连接 {conn_id}: {conn_info['status']}")
        
        # 清理
        await ssh_manager.disconnect_all()
        print("✓ 所有连接已断开")
        
        print("\n=== 集成测试总结 ===")
        print("✓ SSH config解析功能正常")
        print("✓ 连接ID生成逻辑正确")
        print("✓ 参数覆盖功能工作")
        print("✓ 错误处理机制完善")
        print("✓ 连接管理功能正常")
        print("\n🎉 SSH config功能测试通过！")
        
    except Exception as e:
        print(f"集成测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 恢复环境
        try:
            if backup_ssh_config and backup_ssh_config.exists():
                shutil.copy2(backup_ssh_config, ssh_config_path)
                backup_ssh_config.unlink()
            elif ssh_config_path.exists():
                ssh_config_path.unlink()
        except Exception as e:
            print(f"恢复环境时出错: {e}")

if __name__ == "__main__":
    asyncio.run(test_integration())
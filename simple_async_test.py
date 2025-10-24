#!/usr/bin/env python3
"""
简化的异步命令测试
"""
import asyncio
import json
import sys
import time

# 添加项目路径
sys.path.insert(0, '/root/src/sshagent')

from ssh_manager import SSHManager

async def simple_async_test():
    """简单的异步命令测试"""
    print("=== 简化异步命令测试 ===\n")
    
    manager = SSHManager()
    
    try:
        # 建立连接
        print("1. 建立SSH连接...")
        connection_id = await manager.create_connection(
            host="127.0.0.1",
            username="root",
            port=22,
            private_key="/root/.ssh/test_key"
        )
        print(f"   ✓ 连接成功: {connection_id}\n")
        
        # 启动一个简单的长时间运行命令
        print("2. 启动长时间运行命令...")
        command_id = await manager.start_async_command(
            connection_id, "for i in {1..5}; do echo \"Progress: $i/5\"; sleep 1; done"
        )
        print(f"   ✓ 命令已启动: {command_id[:8]}...\n")
        
        # 监控命令执行
        print("3. 监控命令执行...")
        for i in range(7):  # 监控7秒
            await asyncio.sleep(1)
            status = await manager.get_command_status(command_id)
            
            print(f"第{i+1}秒 - 状态: {status['status']}, 运行时长: {status['duration']:.1f}s")
            
            # 显示最新输出
            if status['stdout']:
                lines = status['stdout'].strip().split('\n')
                if lines:
                    print(f"  最新输出: {lines[-1]}")
            
            if status['status'] != 'running':
                print(f"  命令完成，退出码: {status.get('exit_code', 'N/A')}")
                break
        
        # 启动另一个持续命令并测试终止
        print("\n4. 测试命令终止...")
        long_cmd_id = await manager.start_async_command(
            connection_id, "while true; do echo 'Running...'; sleep 1; done"
        )
        print(f"   ✓ 长时间命令已启动: {long_cmd_id[:8]}...")
        
        # 让它运行2秒
        await asyncio.sleep(2)
        
        # 终止命令
        print("   终止命令...")
        success = await manager.terminate_command(long_cmd_id)
        print(f"   终止结果: {success}")
        
        # 检查终止后状态
        await asyncio.sleep(0.5)
        status = await manager.get_command_status(long_cmd_id)
        print(f"   终止后状态: {status['status']}")
        
        # 列出所有命令
        print("\n5. 列出所有命令...")
        all_commands = await manager.list_async_commands()
        print(f"   当前命令数量: {len(all_commands)}")
        for cmd_id, cmd_info in all_commands.items():
            print(f"   - {cmd_id[:8]}...: {cmd_info['status']} ({cmd_info['command'][:30]}...)")
        
        # 清理完成的命令
        print("\n6. 清理完成的命令...")
        cleaned = await manager.cleanup_completed_commands(0)
        print(f"   清理了 {cleaned} 个命令")
        
        # 断开连接
        print("\n7. 断开连接...")
        await manager.disconnect(connection_id)
        print("   ✓ 连接已断开")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await manager.shutdown()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    asyncio.run(simple_async_test())
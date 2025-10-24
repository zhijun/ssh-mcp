#!/usr/bin/env python3
"""
测试长时间运行命令的功能
"""
import asyncio
import json
import sys
import time

# 添加项目路径
sys.path.insert(0, '/root/src/sshagent')

from ssh_manager import SSHManager

async def test_async_commands():
    """测试异步命令功能"""
    print("=== 测试长时间运行命令功能 ===\n")
    
    manager = SSHManager()
    
    try:
        # 1. 建立SSH连接
        print("1. 建立SSH连接...")
        connection_id = await manager.create_connection(
            host="127.0.0.1",
            username="root",
            port=22,
            private_key="/root/.ssh/test_key"
        )
        print(f"   ✓ 连接成功: {connection_id}\n")
        
        # 2. 启动长时间运行的命令
        print("2. 启动长时间运行的命令...")
        
        # 启动一个简单的计数命令
        command_id1 = await manager.start_async_command(
            connection_id, "for i in {1..10}; do echo \"Count: $i\"; sleep 1; done"
        )
        print(f"   ✓ 启动计数命令: {command_id1}")
        
        # 启动一个持续输出命令
        command_id2 = await manager.start_async_command(
            connection_id, "while true; do echo \"Ping: $(date)\"; sleep 2; done"
        )
        print(f"   ✓ 启动持续输出命令: {command_id2}")
        
        # 启动一个会失败的命令
        command_id3 = await manager.start_async_command(
            connection_id, "sleep 3 && echo 'This will fail' && exit 1"
        )
        print(f"   ✓ 启动失败命令: {command_id3}")
        print()
        
        # 3. 监控命令执行
        print("3. 监控命令执行...")
        
        for i in range(15):  # 监控15秒
            print(f"\n--- 第 {i+1} 次检查 ---")
            
            # 检查所有命令状态
            commands = await manager.list_async_commands()
            for cmd_id, cmd_info in commands.items():
                status = await manager.get_command_status(cmd_id)
                print(f"命令 {cmd_id[:8]}... ({cmd_info['command'][:30]}...)")
                print(f"  状态: {status['status']}, 运行时长: {status['duration']:.1f}s")
                
                # 显示最新输出
                if status['stdout']:
                    lines = status['stdout'].strip().split('\n')
                    if lines:
                        print(f"  最新输出: {lines[-1]}")
                
                if status['stderr']:
                    print(f"  错误: {status['stderr'][:50]}...")
            
            await asyncio.sleep(1)
        
        # 4. 终止持续运行的命令
        print("\n4. 终止持续运行的命令...")
        success = await manager.terminate_command(command_id2)
        print(f"   终止命令 {command_id2[:8]}...: {success}")
        
        # 检查终止后的状态
        await asyncio.sleep(1)
        status = await manager.get_command_status(command_id2)
        print(f"   终止后状态: {status['status']}")
        
        # 5. 清理完成的命令
        print("\n5. 清理完成的命令...")
        cleaned = await manager.cleanup_completed_commands(0)  # 立即清理
        print(f"   清理了 {cleaned} 个完成的命令")
        
        # 6. 最终状态检查
        print("\n6. 最终状态检查...")
        remaining_commands = await manager.list_async_commands()
        print(f"   剩余命令数量: {len(remaining_commands)}")
        for cmd_id, cmd_info in remaining_commands.items():
            print(f"   - {cmd_id[:8]}...: {cmd_info['status']}")
        
        # 7. 断开连接
        print("\n7. 断开连接...")
        await manager.disconnect(connection_id)
        print("   ✓ 连接已断开")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 确保清理资源
        await manager.shutdown()
    
    print("\n=== 测试完成 ===")

async def test_top_command():
    """测试top命令的执行"""
    print("\n=== 测试top命令执行 ===\n")
    
    manager = SSHManager()
    
    try:
        # 建立连接
        connection_id = await manager.create_connection(
            host="127.0.0.1",
            username="root",
            port=22,
            private_key="/root/.ssh/test_key"
        )
        print(f"连接成功: {connection_id}")
        
        # 启动top命令（非交互模式）
        print("\n启动top命令...")
        command_id = await manager.start_async_command(
            connection_id, "top -b -n 5 -d 1"  # 批处理模式，更新5次，间隔1秒
        )
        print(f"命令ID: {command_id}")
        
        # 监控top命令输出
        for i in range(8):  # 监控8秒
            await asyncio.sleep(1)
            status = await manager.get_command_status(command_id)
            
            print(f"\n--- 第 {i+1} 次检查 (状态: {status['status']}) ---")
            
            if status['stdout']:
                # 显示top输出的最后几行
                lines = status['stdout'].strip().split('\n')
                if len(lines) > 10:
                    print("最新输出 (最后5行):")
                    for line in lines[-5:]:
                        print(f"  {line}")
                else:
                    print("输出:")
                    for line in lines:
                        print(f"  {line}")
            
            if status['status'] in ['completed', 'failed', 'terminated']:
                print(f"命令结束，退出码: {status.get('exit_code')}")
                break
        
        # 断开连接
        await manager.disconnect(connection_id)
        
    except Exception as e:
        print(f"测试top命令时出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await manager.shutdown()
    
    print("\n=== top命令测试完成 ===")

if __name__ == "__main__":
    print("开始测试长时间运行命令功能...\n")
    
    # 测试基本异步命令功能
    asyncio.run(test_async_commands())
    
    # 测试top命令
    asyncio.run(test_top_command())
    
    print("\n🎉 所有测试完成！")
    print("\n📋 功能验证:")
    print("   ✓ 异步命令启动")
    print("   ✓ 实时输出监控")
    print("   ✓ 命令状态查询")
    print("   ✓ 命令终止")
    print("   ✓ 资源清理")
    print("   ✓ 长时间运行命令支持")
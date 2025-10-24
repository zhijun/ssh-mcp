#!/usr/bin/env python3
"""
简单的MCP SSH Agent测试脚本
"""
import asyncio
import json
import sys
from ssh_manager import SSHManager

async def test_ssh_manager():
    """测试SSH管理器"""
    print("=== 测试SSH管理器 ===")
    
    manager = SSHManager()
    
    # 测试1: 列出连接（应该为空）
    print("1. 测试列出连接...")
    connections = await manager.list_connections()
    print(f"连接列表: {json.dumps(connections, indent=2, ensure_ascii=False)}")
    
    # 测试2: 尝试连接（使用虚拟参数，预期会失败）
    print("\n2. 测试SSH连接（预期失败）...")
    try:
        connection_id = await manager.create_connection(
            host="127.0.0.1",
            username="test",
            password="test"
        )
        print(f"连接ID: {connection_id}")
    except Exception as e:
        print(f"连接失败（符合预期）: {e}")
    
    # 测试3: 获取连接状态
    print("\n3. 测试获取连接状态...")
    status = await manager.get_connection_status("test@127.0.0.1:22")
    print(f"连接状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
    
    print("\n=== SSH管理器测试完成 ===")

if __name__ == "__main__":
    asyncio.run(test_ssh_manager())
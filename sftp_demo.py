#!/usr/bin/env python3
"""
SFTP功能使用示例
演示如何使用SSH Agent MCP的SFTP功能进行文件传输和远程文件管理
"""

import asyncio
import json
from mcp_test_client import MCPTestClient


async def sftp_demo():
    """SFTP功能演示"""
    print("🚀 SSH Agent MCP SFTP功能演示")
    print("=" * 50)
    
    # 创建MCP测试客户端
    client = MCPTestClient()
    
    try:
        # 1. 建立SSH连接
        print("\n📡 步骤1: 建立SSH连接")
        connection_result = await client.call_tool("ssh_connect", {
            "host": "your-server.com",
            "username": "your-username",
            "password": "your-password"
        })
        
        if connection_result.get("isError"):
            print("❌ 连接失败，请检查连接参数")
            return
        
        # 提取连接ID
        connection_text = connection_result["content"][0]["text"]
        connection_id = connection_text.split("连接ID: ")[1].split("\n")[0]
        print(f"✅ 连接成功，连接ID: {connection_id}")
        
        # 2. 列出远程目录
        print("\n📁 步骤2: 列出远程目录")
        list_result = await client.call_tool("ssh_list_remote_directory", {
            "connection_id": connection_id,
            "remote_path": "/home/username"
        })
        
        if not list_result.get("isError"):
            print("✅ 远程目录列表获取成功")
            print(list_result["content"][0]["text"])
        
        # 3. 创建远程目录
        print("\n📂 步骤3: 创建远程目录")
        create_dir_result = await client.call_tool("ssh_create_remote_directory", {
            "connection_id": connection_id,
            "remote_path": "/home/username/mcp_demo",
            "mode": 755,
            "parents": True
        })
        
        if not create_dir_result.get("isError"):
            print("✅ 远程目录创建成功")
            print(create_dir_result["content"][0]["text"])
        
        # 4. 上传文件
        print("\n📤 步骤4: 上传文件")
        upload_result = await client.call_tool("ssh_upload_file", {
            "connection_id": connection_id,
            "local_path": "./demo_file.txt",
            "remote_path": "/home/username/mcp_demo/demo_file.txt"
        })
        
        if not upload_result.get("isError"):
            print("✅ 文件上传成功")
            print(upload_result["content"][0]["text"])
        
        # 5. 获取文件信息
        print("\nℹ️ 步骤5: 获取远程文件信息")
        file_info_result = await client.call_tool("ssh_get_remote_file_info", {
            "connection_id": connection_id,
            "remote_path": "/home/username/mcp_demo/demo_file.txt"
        })
        
        if not file_info_result.get("isError"):
            print("✅ 文件信息获取成功")
            print(file_info_result["content"][0]["text"])
        
        # 6. 下载文件
        print("\n📥 步骤6: 下载文件")
        download_result = await client.call_tool("ssh_download_file", {
            "connection_id": connection_id,
            "remote_path": "/home/username/mcp_demo/demo_file.txt",
            "local_path": "./downloaded_demo_file.txt"
        })
        
        if not download_result.get("isError"):
            print("✅ 文件下载成功")
            print(download_result["content"][0]["text"])
        
        # 7. 重命名文件
        print("\n✏️ 步骤7: 重命名远程文件")
        rename_result = await client.call_tool("ssh_rename_remote_path", {
            "connection_id": connection_id,
            "old_path": "/home/username/mcp_demo/demo_file.txt",
            "new_path": "/home/username/mcp_demo/renamed_file.txt"
        })
        
        if not rename_result.get("isError"):
            print("✅ 文件重命名成功")
            print(rename_result["content"][0]["text"])
        
        # 8. 列出更新后的目录
        print("\n📁 步骤8: 列出更新后的目录")
        updated_list_result = await client.call_tool("ssh_list_remote_directory", {
            "connection_id": connection_id,
            "remote_path": "/home/username/mcp_demo"
        })
        
        if not updated_list_result.get("isError"):
            print("✅ 更新后的目录列表:")
            print(updated_list_result["content"][0]["text"])
        
        # 9. 清理：删除演示目录
        print("\n🗑️ 步骤9: 清理演示目录")
        cleanup_result = await client.call_tool("ssh_remove_remote_file", {
            "connection_id": connection_id,
            "remote_path": "/home/username/mcp_demo"
        })
        
        if not cleanup_result.get("isError"):
            print("✅ 演示目录删除成功")
            print(cleanup_result["content"][0]["text"])
        
        # 10. 断开连接
        print("\n🔌 步骤10: 断开SSH连接")
        disconnect_result = await client.call_tool("ssh_disconnect", {
            "connection_id": connection_id
        })
        
        if not disconnect_result.get("isError"):
            print("✅ SSH连接已断开")
        
        print("\n🎉 SFTP功能演示完成!")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")


async def batch_operations_demo():
    """批量操作演示"""
    print("\n🔄 批量文件操作演示")
    print("=" * 30)
    
    client = MCPTestClient()
    
    # 这里可以添加批量操作的示例代码
    # 例如：批量上传、批量下载、批量重命名等
    
    batch_operations = [
        {
            "action": "upload",
            "local_path": "./file1.txt",
            "remote_path": "/remote/backup/file1.txt"
        },
        {
            "action": "upload",
            "local_path": "./file2.txt",
            "remote_path": "/remote/backup/file2.txt"
        },
        {
            "action": "upload",
            "local_path": "./file3.txt",
            "remote_path": "/remote/backup/file3.txt"
        }
    ]
    
    print("批量操作计划:")
    for i, operation in enumerate(batch_operations, 1):
        print(f"  {i}. {operation['action']}: {operation['local_path']} -> {operation['remote_path']}")
    
    print("\n💡 提示: 在实际使用中，您可以通过循环或并发执行这些操作")


def create_demo_file():
    """创建演示文件"""
    demo_content = """这是一个演示文件
用于测试SSH Agent MCP的SFTP功能

创建时间: 2024-01-15
文件用途: SFTP功能演示

内容示例:
- 文件上传测试
- 文件下载测试
- 文件信息查询
- 文件重命名测试
"""
    
    with open("./demo_file.txt", "w", encoding="utf-8") as f:
        f.write(demo_content)
    
    print("📝 演示文件已创建: demo_file.txt")


if __name__ == "__main__":
    print("🎯 SSH Agent MCP SFTP功能演示程序")
    print("使用前请确保:")
    print("1. 已正确配置SSH连接参数")
    print("2. 有足够的权限进行文件操作")
    print("3. 网络连接正常")
    
    # 创建演示文件
    create_demo_file()
    
    # 运行演示
    print("\n开始SFTP功能演示...")
    # asyncio.run(sftp_demo())
    
    # 显示批量操作示例
    asyncio.run(batch_operations_demo())
    
    print("\n✨ 演示程序准备完成!")
    print("要运行实际演示，请:")
    print("1. 修改连接参数为实际值")
    print("2. 取消注释 asyncio.run(sftp_demo())")
    print("3. 运行程序")
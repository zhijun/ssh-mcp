#!/usr/bin/env python3
"""
简单的SFTP功能测试
"""

import asyncio
import tempfile
import os
from unittest.mock import Mock, patch
from ssh_manager import SSHManager, ConnectionStatus


async def test_sftp_functionality():
    """测试SFTP功能"""
    print("🧪 开始SFTP功能测试...")
    
    ssh_manager = SSHManager()
    connection_id = "test_connection"
    
    # 创建模拟连接
    mock_connection = Mock()
    mock_connection.status = ConnectionStatus.CONNECTED
    mock_connection.client = Mock()
    
    # 创建模拟SFTP客户端
    mock_sftp = Mock()
    mock_connection.client.open_sftp.return_value = mock_sftp
    
    # 添加到管理器
    ssh_manager.connections[connection_id] = mock_connection
    
    try:
        # 测试1: 上传文件
        print("\n📤 测试文件上传...")
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file.flush()
            local_path = temp_file.name
        
        try:
            # 模拟SFTP操作
            mock_sftp.put.return_value = None
            mock_sftp.stat.return_value = Mock(st_size=len("test content"))
            
            with patch('os.path.getsize', return_value=len("test content")):
                result = await ssh_manager.upload_file(
                    connection_id,
                    local_path,
                    "/remote/path/test.txt"
                )
            
            if result['success']:
                print("✅ 文件上传测试通过")
            else:
                print(f"❌ 文件上传测试失败: {result.get('error', '未知错误')}")
                
        finally:
            os.unlink(local_path)
        
        # 测试2: 下载文件
        print("\n📥 测试文件下载...")
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, "downloaded_file.txt")
            
            # 模拟SFTP操作
            mock_sftp.stat.return_value = Mock(st_size=len("test content"))
            mock_sftp.get.return_value = None
            
            with patch('os.path.getsize', return_value=len("test content")):
                with patch('os.makedirs'):
                    result = await ssh_manager.download_file(
                        connection_id,
                        "/remote/path/test.txt",
                        local_path
                    )
            
            if result['success']:
                print("✅ 文件下载测试通过")
            else:
                print(f"❌ 文件下载测试失败: {result.get('error', '未知错误')}")
        
        # 测试3: 列出远程目录
        print("\n📁 测试列出远程目录...")
        
        # 模拟文件属性
        mock_file1 = Mock()
        mock_file1.filename = "file1.txt"
        mock_file1.st_size = 1024
        mock_file1.st_mtime = 1640995200  # 2022-01-01
        mock_file1.st_mode = 0o100644  # 普通文件
        mock_file1.st_uid = 1000
        mock_file1.st_gid = 1000
        
        mock_dir1 = Mock()
        mock_dir1.filename = "directory1"
        mock_dir1.st_size = 4096
        mock_dir1.st_mtime = 1640995200
        mock_dir1.st_mode = 0o040755  # 目录
        mock_dir1.st_uid = 1000
        mock_dir1.st_gid = 1000
        
        mock_sftp.listdir_attr.return_value = [mock_file1, mock_dir1]
        
        result = await ssh_manager.list_remote_directory(
            connection_id,
            "/remote/path"
        )
        
        if result['success'] and result['total_count'] == 2:
            print("✅ 列出远程目录测试通过")
        else:
            print(f"❌ 列出远程目录测试失败: {result.get('error', '未知错误')}")
        
        # 测试4: 创建远程目录
        print("\n📂 测试创建远程目录...")
        mock_sftp.mkdir.return_value = None
        
        result = await ssh_manager.create_remote_directory(
            connection_id,
            "/remote/new_directory",
            mode=0o755,
            parents=True
        )
        
        if result['success']:
            print("✅ 创建远程目录测试通过")
        else:
            print(f"❌ 创建远程目录测试失败: {result.get('error', '未知错误')}")
        
        # 测试5: 删除远程文件
        print("\n🗑️ 测试删除远程文件...")
        
        # 模拟文件属性（普通文件）
        mock_file = Mock()
        mock_file.st_mode = 0o100644  # 普通文件
        
        mock_sftp.stat.return_value = mock_file
        mock_sftp.remove.return_value = None
        
        result = await ssh_manager.remove_remote_file(
            connection_id,
            "/remote/path/file.txt"
        )
        
        if result['success'] and result['type'] == "文件":
            print("✅ 删除远程文件测试通过")
        else:
            print(f"❌ 删除远程文件测试失败: {result.get('error', '未知错误')}")
        
        # 测试6: 获取远程文件信息
        print("\nℹ️ 测试获取远程文件信息...")
        
        # 模拟文件属性
        mock_file = Mock()
        mock_file.st_size = 2048
        mock_file.st_mtime = 1640995200
        mock_file.st_atime = 1640995300
        mock_file.st_mode = 0o100644
        mock_file.st_uid = 1000
        mock_file.st_gid = 1000
        
        mock_sftp.stat.return_value = mock_file
        
        result = await ssh_manager.get_remote_file_info(
            connection_id,
            "/remote/path/file.txt"
        )
        
        if result['success'] and result['size'] == 2048:
            print("✅ 获取远程文件信息测试通过")
        else:
            print(f"❌ 获取远程文件信息测试失败: {result.get('error', '未知错误')}")
        
        # 测试7: 重命名远程路径
        print("\n✏️ 测试重命名远程路径...")
        mock_sftp.rename.return_value = None
        
        result = await ssh_manager.rename_remote_path(
            connection_id,
            "/remote/path/old_name.txt",
            "/remote/path/new_name.txt"
        )
        
        if result['success']:
            print("✅ 重命名远程路径测试通过")
        else:
            print(f"❌ 重命名远程路径测试失败: {result.get('error', '未知错误')}")
        
        # 测试8: 连接不存在的情况
        print("\n❌ 测试连接不存在的情况...")
        try:
            result = await ssh_manager.upload_file(
                "invalid_connection",
                "/local/path",
                "/remote/path"
            )
            print("应该抛出异常但没有")
        except Exception as e:
            if "连接不存在" in str(e):
                print("✅ 连接不存在异常处理正确")
            else:
                print(f"❌ 异常处理不正确: {e}")
        
        print("\n🎉 所有SFTP功能测试完成!")
        
    finally:
        # 清理连接
        if connection_id in ssh_manager.connections:
            del ssh_manager.connections[connection_id]


def _format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


if __name__ == "__main__":
    asyncio.run(test_sftp_functionality())
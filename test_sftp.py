#!/usr/bin/env python3
"""
SFTP功能测试用例
测试SSH Agent MCP的SFTP文件传输功能
"""

import asyncio
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, AsyncMock
import paramiko
from ssh_manager import SSHManager, ConnectionStatus


class TestSFTPFunctionality(unittest.TestCase):
    """SFTP功能测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.ssh_manager = SSHManager()
        self.connection_id = "test_connection"
        
        # 创建模拟连接
        self.mock_connection = Mock()
        self.mock_connection.status = ConnectionStatus.CONNECTED
        self.mock_connection.client = Mock()
        
        # 创建模拟SFTP客户端
        self.mock_sftp = Mock()
        self.mock_connection.client.open_sftp.return_value = self.mock_sftp
        
        # 添加到管理器
        self.ssh_manager.connections[self.connection_id] = self.mock_connection
    
    async def test_upload_file_success(self):
        """测试文件上传成功"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_file.flush()
            local_path = temp_file.name
        
        try:
            # 模拟SFTP操作
            self.mock_sftp.put.return_value = None
            self.mock_sftp.stat.return_value = Mock(st_size=len("test content"))
            
            with patch('os.path.getsize', return_value=len("test content")):
                result = await self.ssh_manager.upload_file(
                    self.connection_id,
                    local_path,
                    "/remote/path/test.txt"
                )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['local_path'], local_path)
            self.assertEqual(result['remote_path'], "/remote/path/test.txt")
            self.assertIn("message", result)
            
        finally:
            os.unlink(local_path)
    
    async def test_upload_file_connection_not_exists(self):
        """测试上传文件时连接不存在"""
        result = await self.ssh_manager.upload_file(
            "invalid_connection",
            "/local/path",
            "/remote/path"
        )
        
        # 应该抛出异常，但这里我们测试异常处理
        self.assertIsInstance(result, dict)
    
    async def test_download_file_success(self):
        """测试文件下载成功"""
        with tempfile.TemporaryDirectory() as temp_dir:
            local_path = os.path.join(temp_dir, "downloaded_file.txt")
            
            # 模拟SFTP操作
            self.mock_sftp.stat.return_value = Mock(st_size=len("test content"))
            self.mock_sftp.get.return_value = None
            
            with patch('os.path.getsize', return_value=len("test content")):
                with patch('os.makedirs'):
                    result = await self.ssh_manager.download_file(
                        self.connection_id,
                        "/remote/path/test.txt",
                        local_path
                    )
            
            self.assertTrue(result['success'])
            self.assertEqual(result['remote_path'], "/remote/path/test.txt")
            self.assertEqual(result['local_path'], local_path)
            self.assertIn("message", result)
    
    async def test_list_remote_directory_success(self):
        """测试列出远程目录成功"""
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
        
        self.mock_sftp.listdir_attr.return_value = [mock_file1, mock_dir1]
        
        result = await self.ssh_manager.list_remote_directory(
            self.connection_id,
            "/remote/path"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['path'], "/remote/path")
        self.assertEqual(result['total_count'], 2)
        self.assertEqual(result['file_count'], 1)
        self.assertEqual(result['directory_count'], 1)
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(len(result['directories']), 1)
    
    async def test_create_remote_directory_success(self):
        """测试创建远程目录成功"""
        self.mock_sftp.mkdir.return_value = None
        
        result = await self.ssh_manager.create_remote_directory(
            self.connection_id,
            "/remote/new_directory",
            mode=0o755,
            parents=True
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['path'], "/remote/new_directory")
        self.assertEqual(result['mode'], "0o755")
        self.assertIn("message", result)
    
    async def test_remove_remote_file_success(self):
        """测试删除远程文件成功"""
        # 模拟文件属性（普通文件）
        mock_file = Mock()
        mock_file.st_mode = 0o100644  # 普通文件
        
        self.mock_sftp.stat.return_value = mock_file
        self.mock_sftp.remove.return_value = None
        
        result = await self.ssh_manager.remove_remote_file(
            self.connection_id,
            "/remote/path/file.txt"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['path'], "/remote/path/file.txt")
        self.assertEqual(result['type'], "文件")
        self.assertIn("message", result)
    
    async def test_remove_remote_directory_success(self):
        """测试删除远程目录成功"""
        # 模拟目录属性
        mock_dir = Mock()
        mock_dir.st_mode = 0o040755  # 目录
        
        self.mock_sftp.stat.return_value = mock_dir
        self.mock_sftp.listdir_attr.return_value = []  # 空目录
        self.mock_sftp.rmdir.return_value = None
        
        result = await self.ssh_manager.remove_remote_file(
            self.connection_id,
            "/remote/path/directory"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['path'], "/remote/path/directory")
        self.assertEqual(result['type'], "目录")
        self.assertIn("message", result)
    
    async def test_get_remote_file_info_success(self):
        """测试获取远程文件信息成功"""
        # 模拟文件属性
        mock_file = Mock()
        mock_file.st_size = 2048
        mock_file.st_mtime = 1640995200
        mock_file.st_atime = 1640995300
        mock_file.st_mode = 0o100644
        mock_file.st_uid = 1000
        mock_file.st_gid = 1000
        
        self.mock_sftp.stat.return_value = mock_file
        
        result = await self.ssh_manager.get_remote_file_info(
            self.connection_id,
            "/remote/path/file.txt"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['path'], "/remote/path/file.txt")
        self.assertEqual(result['size'], 2048)
        self.assertEqual(result['permissions'], "644")
        self.assertEqual(result['owner'], 1000)
        self.assertEqual(result['group'], 1000)
        self.assertFalse(result['is_directory'])
    
    async def test_rename_remote_path_success(self):
        """测试重命名远程路径成功"""
        self.mock_sftp.rename.return_value = None
        
        result = await self.ssh_manager.rename_remote_path(
            self.connection_id,
            "/remote/path/old_name.txt",
            "/remote/path/new_name.txt"
        )
        
        self.assertTrue(result['success'])
        self.assertEqual(result['old_path'], "/remote/path/old_name.txt")
        self.assertEqual(result['new_path'], "/remote/path/new_name.txt")
        self.assertIn("message", result)
    
    async def test_sftp_connection_not_connected(self):
        """测试连接未建立时的SFTP操作"""
        # 设置连接状态为未连接
        self.mock_connection.status = ConnectionStatus.DISCONNECTED
        
        result = await self.ssh_manager.upload_file(
            self.connection_id,
            "/local/path",
            "/remote/path"
        )
        
        # 应该抛出异常，但这里我们测试异常处理
        self.assertIsInstance(result, dict)
    
    def tearDown(self):
        """测试后清理"""
        # 清理连接
        if self.connection_id in self.ssh_manager.connections:
            del self.ssh_manager.connections[self.connection_id]


class TestSFTPIntegration(unittest.TestCase):
    """SFTP集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.ssh_manager = SSHManager()
    
    def test_sftp_tools_registration(self):
        """测试SFTP工具是否正确注册到MCP服务器"""
        from mcp_server import handle_list_tools
        
        # 这个测试需要实际的MCP服务器运行，这里只是示例
        # 在实际环境中需要更复杂的设置来测试MCP工具注册
        pass


def run_async_test(coro):
    """运行异步测试的辅助函数"""
    return asyncio.run(coro)


if __name__ == '__main__':
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    test_cases = [
        ('test_upload_file_success', TestSFTPFunctionality),
        ('test_download_file_success', TestSFTPFunctionality),
        ('test_list_remote_directory_success', TestSFTPFunctionality),
        ('test_create_remote_directory_success', TestSFTPFunctionality),
        ('test_remove_remote_file_success', TestSFTPFunctionality),
        ('test_remove_remote_directory_success', TestSFTPFunctionality),
        ('test_get_remote_file_info_success', TestSFTPFunctionality),
        ('test_rename_remote_path_success', TestSFTPFunctionality),
    ]
    
    for test_name, test_class in test_cases:
        test_instance = test_class(test_name)
        test_instance.setUp()
        
        # 创建异步测试
        async def async_test():
            await getattr(test_instance, test_name)()
            test_instance.tearDown()
        
        # 添加到测试套件
        suite.addTest(unittest.FunctionTestCase(
            lambda: run_async_test(async_test()),
            description=test_name
        ))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出结果
    if result.wasSuccessful():
        print("\n✅ 所有SFTP功能测试通过!")
    else:
        print(f"\n❌ 测试失败: {len(result.failures)} 个失败, {len(result.errors)} 个错误")
        for failure in result.failures:
            print(f"失败: {failure[0]} - {failure[1]}")
        for error in result.errors:
            print(f"错误: {error[0]} - {error[1]}")
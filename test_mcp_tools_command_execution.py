#!/usr/bin/env python3
"""
MCP命令执行工具的pytest测试
测试ssh_execute等命令执行工具
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from mcp_server import handle_call_tool, ssh_manager
from mcp.types import CallToolResult, TextContent
from ssh_manager import ConnectionStatus


class TestCommandExecutionTools:
    """命令执行工具测试类"""
    
    @pytest.mark.asyncio
    async def test_ssh_execute_success(self):
        """测试ssh_execute成功"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "exit_code": 0,
                "stdout": "Hello, World!",
                "stderr": ""
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "echo 'Hello, World!'"
            })
            
            assert isinstance(result, CallToolResult)
            assert not result.isError
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            
            text = result.content[0].text
            assert "Hello, World!" in text
            assert "退出码: 0" in text
            assert "echo 'Hello, World!'" in text
            assert "成功: True" in text
            
            mock_execute.assert_called_once_with(
                connection_id="user@server.com:22",
                command="echo 'Hello, World!'",
                timeout=30  # 默认超时
            )
    
    @pytest.mark.asyncio
    async def test_ssh_execute_with_timeout(self):
        """测试ssh_execute指定超时"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "exit_code": 0,
                "stdout": "Command completed",
                "stderr": ""
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "sleep 1",
                "timeout": 60
            })
            
            assert not result.isError
            text = result.content[0].text
            assert "Command completed" in text
            
            mock_execute.assert_called_once_with(
                connection_id="user@server.com:22",
                command="sleep 1",
                timeout=60
            )
    
    @pytest.mark.asyncio
    async def test_ssh_execute_command_failure(self):
        """测试ssh_execute命令执行失败"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "exit_code": 1,
                "stdout": "",
                "stderr": "command not found"
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "nonexistent_command"
            })
            
            assert result.isError  # 命令失败算工具错误
            text = result.content[0].text
            assert "退出码: 1" in text
            assert "command not found" in text
            assert "nonexistent_command" in text
            assert "成功: False" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_connection_not_found(self):
        """测试ssh_execute连接不存在"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "连接不存在"
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "nonexistent@server.com:22",
                "command": "ls"
            })
            
            assert result.isError  # 连接问题算工具错误
            text = result.content[0].text
            assert "连接不存在" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_missing_connection_id(self):
        """测试ssh_execute缺少连接ID"""
        result = await handle_call_tool("ssh_execute", {
            "command": "ls"
            # 缺少connection_id
        })
        
        assert result.isError
        text = result.content[0].text
        assert "Field required" in text or "connection_id" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_missing_command(self):
        """测试ssh_execute缺少命令"""
        result = await handle_call_tool("ssh_execute", {
            "connection_id": "user@server.com:22"
            # 缺少command
        })
        
        assert result.isError
        text = result.content[0].text
        assert "Field required" in text or "command" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_with_output(self):
        """测试ssh_execute有输出的命令"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "exit_code": 0,
                "stdout": "file1.txt\nfile2.txt\ndirectory/\n",
                "stderr": ""
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "ls -la"
            })
            
            assert not result.isError
            text = result.content[0].text
            assert "file1.txt" in text
            assert "file2.txt" in text
            assert "directory/" in text
            assert "ls -la" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_with_stderr(self):
        """测试ssh_execute有stderr输出的命令"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": False,  # 有stderr通常意味着失败
                "exit_code": 2,
                "stdout": "Some output",
                "stderr": "Warning: Something went wrong"
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "test_command"
            })
            
            assert result.isError
            text = result.content[0].text
            assert "Some output" in text
            assert "Warning: Something went wrong" in text
            assert "退出码: 2" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_timeout_error(self):
        """测试ssh_execute超时错误"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.side_effect = asyncio.TimeoutError("命令执行超时")
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "sleep 100"
            })
            
            assert result.isError
            text = result.content[0].text
            assert "超时" in text or "timeout" in text.lower()
    
    @pytest.mark.asyncio
    async def test_ssh_execute_complex_command(self):
        """测试ssh_execute复杂命令"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "exit_code": 0,
                "stdout": "total 16\ndrwxr-xr-x 2 user user 4096 Jan 15 10:30 .\ndrwxr-xr-x 3 user user 4096 Jan 15 10:25 ..\n-rw-r--r-- 1 user user   45 Jan 15 10:30 file.txt\n",
                "stderr": ""
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "ls -la /home/user"
            })
            
            assert not result.isError
            text = result.content[0].text
            assert "total 16" in text
            assert "file.txt" in text
            assert "ls -la /home/user" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_empty_output(self):
        """测试ssh_execute空输出"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "exit_code": 0,
                "stdout": "",
                "stderr": ""
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "true"
            })
            
            assert not result.isError
            text = result.content[0].text
            assert "退出码: 0" in text
            assert "true" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_parameter_validation(self):
        """测试ssh_execute参数验证"""
        # 测试各种参数类型
        result = await handle_call_tool("ssh_execute", {
            "connection_id": "user@server.com:22",
            "command": "echo test",
            "timeout": "30"  # 字符串而不是数字
        })
        
        # 应该能处理参数类型转换
        assert isinstance(result, CallToolResult)
    
    @pytest.mark.asyncio
    async def test_ssh_execute_long_command(self):
        """测试ssh_execute长命令"""
        long_command = "echo 'This is a very long command that contains many words and should still be handled properly by the SSH execute function without any issues or truncation'"
        
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "exit_code": 0,
                "stdout": "This is a very long command that contains many words and should still be handled properly by the SSH execute function without any issues or truncation\n",
                "stderr": ""
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": long_command
            })
            
            assert not result.isError
            text = result.content[0].text
            assert "handled properly" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_special_characters(self):
        """测试ssh_execute特殊字符"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "exit_code": 0,
                "stdout": "Special chars: !@#$%^&*()_+-={}[]|\\:;\"'<>?,./",
                "stderr": ""
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "echo 'Special chars: !@#$%^&*()_+-={}[]|\\:;\"'<>?,./'"
            })
            
            assert not result.isError
            text = result.content[0].text
            assert "Special chars:" in text
            assert "!@#$%^&*()" in text
    
    @pytest.mark.asyncio
    async def test_ssh_execute_connection_failed(self):
        """测试ssh_execute连接失败"""
        with patch('ssh_manager.SSHManager.execute_command') as mock_execute:
            mock_execute.return_value = {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "连接失败: 连接超时"
            }
            
            result = await handle_call_tool("ssh_execute", {
                "connection_id": "user@server.com:22",
                "command": "ls"
            })
            
            assert result.isError
            text = result.content[0].text
            assert "连接失败" in text
            assert "连接超时" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
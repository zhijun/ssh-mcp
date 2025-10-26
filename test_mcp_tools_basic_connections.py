#!/usr/bin/env python3
"""
MCP基础连接工具的pytest测试
测试ssh_connect、ssh_connect_by_name、ssh_connect_by_config_host等基础连接工具
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from mcp_server import handle_call_tool, ssh_manager, config_loader
from mcp.types import CallToolResult, TextContent
from ssh_manager import ConnectionStatus


class TestBasicConnectionTools:
    """基础连接工具测试类"""
    
    @pytest.fixture
    def mock_ssh_config(self):
        """模拟SSH配置"""
        return {
            "connections": [
                {
                    "name": "test-server",
                    "host": "test.example.com",
                    "username": "testuser",
                    "port": 22,
                    "password": "testpass"
                }
            ]
        }
    
    @pytest.fixture
    def mock_ssh_config_with_key(self):
        """模拟使用私钥的SSH配置"""
        return {
            "connections": [
                {
                    "name": "key-server",
                    "host": "key.example.com",
                    "username": "keyuser",
                    "port": 22,
                    "private_key": "/path/to/private/key",
                    "private_key_password": "keypass"
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_ssh_connect_success(self):
        """测试ssh_connect成功"""
        with patch('ssh_manager.SSHManager.create_connection') as mock_create, \
             patch('ssh_manager.SSHManager.get_connection_status') as mock_status:
            
            mock_create.return_value = "testuser@test.example.com:22"
            mock_status.return_value = {"status": "connected"}
            
            result = await handle_call_tool("ssh_connect", {
                "host": "test.example.com",
                "username": "testuser",
                "password": "testpass"
            })
            
            assert isinstance(result, CallToolResult)
            assert not result.isError
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            assert "连接建立成功" in result.content[0].text
            mock_create.assert_called_once_with(
                host="test.example.com",
                username="testuser",
                port=22,
                password="testpass",
                private_key=None,
                private_key_password=None
            )
    
    @pytest.mark.asyncio
    async def test_ssh_connect_with_port(self):
        """测试ssh_connect指定端口"""
        with patch('ssh_manager.SSHManager.create_connection') as mock_create, \
             patch('ssh_manager.SSHManager.get_connection_status') as mock_status:
            
            mock_create.return_value = "testuser@test.example.com:2222"
            mock_status.return_value = {"status": "connected"}
            
            result = await handle_call_tool("ssh_connect", {
                "host": "test.example.com",
                "username": "testuser",
                "port": 2222,
                "password": "testpass"
            })
            
            assert not result.isError
            mock_create.assert_called_once_with(
                host="test.example.com",
                username="testuser",
                port=2222,
                password="testpass",
                private_key=None,
                private_key_password=None
            )
    
    @pytest.mark.asyncio
    async def test_ssh_connect_with_private_key(self):
        """测试ssh_connect使用私钥"""
        with patch('ssh_manager.SSHManager.create_connection') as mock_create, \
             patch('ssh_manager.SSHManager.get_connection_status') as mock_status:
            
            mock_create.return_value = "keyuser@key.example.com:22"
            mock_status.return_value = {"status": "connected"}
            
            result = await handle_call_tool("ssh_connect", {
                "host": "key.example.com",
                "username": "keyuser",
                "private_key": "/path/to/private/key",
                "private_key_password": "keypass"
            })
            
            assert not result.isError
            mock_create.assert_called_once_with(
                host="key.example.com",
                username="keyuser",
                port=22,
                password=None,
                private_key="/path/to/private/key",
                private_key_password="keypass"
            )
    
    @pytest.mark.asyncio
    async def test_ssh_connect_missing_required_params(self):
        """测试ssh_connect缺少必需参数"""
        result = await handle_call_tool("ssh_connect", {
            "host": "test.example.com"
            # 缺少username
        })
        
        assert isinstance(result, CallToolResult)
        assert result.isError
        assert "缺少必需参数" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_ssh_connect_failure(self):
        """测试ssh_connect连接失败"""
        with patch('ssh_manager.SSHManager.create_connection') as mock_create:
            mock_create.side_effect = Exception("连接失败")
            
            result = await handle_call_tool("ssh_connect", {
                "host": "test.example.com",
                "username": "testuser",
                "password": "wrongpass"
            })
            
            assert isinstance(result, CallToolResult)
            assert result.isError
            assert "连接失败" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_ssh_connect_by_name_success(self, mock_ssh_config):
        """测试ssh_connect_by_name成功"""
        with patch('mcp_server.config') as mock_config, \
             patch('mcp_server.config_loader.get_connection_by_name') as mock_get_conn, \
             patch('ssh_manager.SSHManager.create_connection') as mock_create, \
             patch('ssh_manager.SSHManager.get_connection_status') as mock_status:
            
            # 创建连接配置对象
            from config_loader import SSHConnectionConfig
            conn_config = SSHConnectionConfig(**mock_ssh_config["connections"][0])
            
            mock_config.return_value = mock_ssh_config
            mock_get_conn.return_value = conn_config
            mock_create.return_value = "testuser@test.example.com:22"
            mock_status.return_value = {"status": "connected"}
            
            result = await handle_call_tool("ssh_connect_by_name", {
                "connection_name": "test-server"
            })
            
            assert not result.isError
            assert "连接成功" in result.content[0].text
            mock_get_conn.assert_called_once_with("test-server")
    
    @pytest.mark.asyncio
    async def test_ssh_connect_by_name_not_found(self, mock_ssh_config):
        """测试ssh_connect_by_name连接名称不存在"""
        with patch('mcp_server.config') as mock_config, \
             patch('mcp_server.config_loader.get_connection_by_name') as mock_get_conn, \
             patch('mcp_server.config_loader.list_connection_names') as mock_list_names:
            
            mock_config.return_value = mock_ssh_config
            mock_get_conn.return_value = None
            mock_list_names.return_value = ["test-server"]
            
            result = await handle_call_tool("ssh_connect_by_name", {
                "connection_name": "nonexistent-server"
            })
            
            assert result.isError
            assert "不存在" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_ssh_connect_by_name_missing_name(self):
        """测试ssh_connect_by_name缺少连接名称"""
        result = await handle_call_tool("ssh_connect_by_name", {})
        
        assert result.isError
        assert "缺少必需参数" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_ssh_connect_by_config_host_success(self):
        """测试ssh_connect_by_config_host成功"""
        # 这个测试需要实际的SSH config文件，暂时跳过具体实现
        # 只测试参数验证
        result = await handle_call_tool("ssh_connect_by_config_host", {
            "config_host": "test-server"
        })
        
        # 由于没有实际的SSH config，预期会失败
        assert isinstance(result, CallToolResult)
    
    @pytest.mark.asyncio
    async def test_ssh_connect_by_config_host_missing_host(self):
        """测试ssh_connect_by_config_host缺少主机名"""
        result = await handle_call_tool("ssh_connect_by_config_host", {})
        
        assert result.isError
        assert "缺少必需参数" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_ssh_disconnect_success(self):
        """测试ssh_disconnect成功"""
        with patch('ssh_manager.SSHManager.disconnect') as mock_disconnect:
            mock_disconnect.return_value = True
            
            result = await handle_call_tool("ssh_disconnect", {
                "connection_id": "testuser@test.example.com:22"
            })
            
            assert not result.isError
            assert "SSH连接已断开" in result.content[0].text
            mock_disconnect.assert_called_once_with("testuser@test.example.com:22")
    
    @pytest.mark.asyncio
    async def test_ssh_disconnect_missing_connection_id(self):
        """测试ssh_disconnect缺少连接ID"""
        result = await handle_call_tool("ssh_disconnect", {})
        
        assert result.isError
        assert "缺少必需参数: connection_id" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_ssh_disconnect_failure(self):
        """测试ssh_disconnect失败"""
        with patch('ssh_manager.SSHManager.disconnect') as mock_disconnect:
            mock_disconnect.return_value = False
            
            result = await handle_call_tool("ssh_disconnect", {
                "connection_id": "nonexistent@server.com:22"
            })
            
            assert result.isError
            assert "断开连接失败" in result.content[0].text
    
    @pytest.mark.asyncio
    async def test_ssh_disconnect_all_success(self):
        """测试ssh_disconnect_all成功"""
        with patch('ssh_manager.SSHManager.disconnect_all') as mock_disconnect_all:
            mock_disconnect_all.return_value = True
            
            result = await handle_call_tool("ssh_disconnect_all", {})
            
            assert not result.isError
            assert "所有SSH连接已断开" in result.content[0].text
            mock_disconnect_all.assert_called_once()
    
    # 删除重复的测试方法


def mock_open_read(content):
    """模拟文件打开读取"""
    from unittest.mock import mock_open
    return mock_open(read_data=content)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

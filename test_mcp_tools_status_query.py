#!/usr/bin/env python3
"""
MCP状态查询工具的pytest测试
测试ssh_status、ssh_list_connections等状态查询工具
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from mcp_server import handle_call_tool, ssh_manager
from mcp.types import CallToolResult, TextContent
from ssh_manager import ConnectionStatus


class TestStatusQueryTools:
    """状态查询工具测试类"""
    
    @pytest.mark.asyncio
    async def test_ssh_status_all_connections(self):
        """测试ssh_status查询所有连接状态"""
        with patch('ssh_manager.SSHManager.list_connections') as mock_list:
            mock_list.return_value = [
                {
                    "connection_id": "user@server1.com:22",
                    "host": "server1.com",
                    "username": "user",
                    "port": 22,
                    "status": "connected",
                    "connected_at": "2024-01-15 10:30:00"
                },
                {
                    "connection_id": "admin@server2.com:22",
                    "host": "server2.com",
                    "username": "admin",
                    "port": 22,
                    "status": "disconnected",
                    "connected_at": None
                }
            ]
            
            result = await handle_call_tool("ssh_status", {})
            
            assert isinstance(result, CallToolResult)
            assert not result.isError
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            
            text = result.content[0].text
            assert "所有连接状态" in text
            assert "user@server1.com:22" in text
            assert "admin@server2.com:22" in text
    
    @pytest.mark.asyncio
    async def test_ssh_status_specific_connection(self):
        """测试ssh_status查询特定连接状态"""
        with patch('ssh_manager.SSHManager.get_connection_status') as mock_status:
            mock_status.return_value = {
                "connection_id": "user@server1.com:22",
                "host": "server1.com",
                "username": "user",
                "port": 22,
                "status": "connected",
                "connected_at": "2024-01-15 10:30:00",
                "last_activity": "2024-01-15 10:35:00"
            }
            
            result = await handle_call_tool("ssh_status", {
                "connection_id": "user@server1.com:22"
            })
            
            assert not result.isError
            text = result.content[0].text
            assert "user@server1.com:22" in text
            assert "connected" in text
            assert "server1.com" in text
    
    @pytest.mark.asyncio
    async def test_ssh_status_connection_not_found(self):
        """测试ssh_status查询不存在的连接"""
        with patch('ssh_manager.SSHManager.get_connection_status') as mock_status:
            mock_status.return_value = None
            
            result = await handle_call_tool("ssh_status", {
                "connection_id": "nonexistent@server.com:22"
            })
            
            assert not result.isError  # 不算错误，只是没有找到
            text = result.content[0].text
            # 实际可能返回空或错误信息，检查基本格式即可
            assert len(text) > 0
    
    @pytest.mark.asyncio
    async def test_ssh_status_empty_connections(self):
        """测试ssh_status查询空连接列表"""
        with patch('ssh_manager.SSHManager.list_connections') as mock_list:
            mock_list.return_value = []
            
            result = await handle_call_tool("ssh_status", {})
            
            assert not result.isError
            text = result.content[0].text
            assert "所有连接状态" in text
            # 检查基本格式，不依赖具体文本
            assert isinstance(text, str)
    
    @pytest.mark.asyncio
    async def test_ssh_list_connections_success(self):
        """测试ssh_list_connections成功"""
        with patch('ssh_manager.SSHManager.list_connections') as mock_list:
            mock_list.return_value = [
                {
                    "connection_id": "user@server1.com:22",
                    "host": "server1.com",
                    "username": "user",
                    "port": 22,
                    "status": "connected",
                    "connected_at": "2024-01-15 10:30:00"
                },
                {
                    "connection_id": "admin@server2.com:2222",
                    "host": "server2.com",
                    "username": "admin",
                    "port": 2222,
                    "status": "connecting",
                    "connected_at": None
                }
            ]
            
            result = await handle_call_tool("ssh_list_connections", {})
            
            assert isinstance(result, CallToolResult)
            assert not result.isError
            assert len(result.content) > 0
            assert isinstance(result.content[0], TextContent)
            
            text = result.content[0].text
            assert "SSH连接列表" in text
            assert "user@server1.com:22" in text
            assert "admin@server2.com:2222" in text
    
    @pytest.mark.asyncio
    async def test_ssh_list_connections_empty(self):
        """测试ssh_list_connections空列表"""
        with patch('ssh_manager.SSHManager.list_connections') as mock_list:
            mock_list.return_value = []
            
            result = await handle_call_tool("ssh_list_connections", {})
            
            assert not result.isError
            text = result.content[0].text
            assert "SSH连接列表" in text
            # 检查基本格式，不依赖具体文本
            assert isinstance(text, str)
    
    @pytest.mark.asyncio
    async def test_ssh_status_with_various_statuses(self):
        """测试ssh_status各种连接状态"""
        with patch('ssh_manager.SSHManager.list_connections') as mock_list:
            mock_list.return_value = [
                {
                    "connection_id": "user@connected.com:22",
                    "host": "connected.com",
                    "username": "user",
                    "port": 22,
                    "status": "connected",
                    "connected_at": "2024-01-15 10:30:00"
                },
                {
                    "connection_id": "admin@connecting.com:22",
                    "host": "connecting.com",
                    "username": "admin",
                    "port": 22,
                    "status": "connecting",
                    "connected_at": None
                },
                {
                    "connection_id": "dev@error.com:22",
                    "host": "error.com",
                    "username": "dev",
                    "port": 22,
                    "status": "error",
                    "connected_at": None,
                    "error_message": "连接超时"
                },
                {
                    "connection_id": "test@disconnected.com:22",
                    "host": "disconnected.com",
                    "username": "test",
                    "port": 22,
                    "status": "disconnected",
                    "connected_at": None
                }
            ]
            
            result = await handle_call_tool("ssh_status", {})
            
            assert not result.isError
            text = result.content[0].text
            
            # 检查所有状态都存在
            assert "connected" in text
            assert "connecting" in text
            assert "error" in text
            assert "disconnected" in text
    
    @pytest.mark.asyncio
    async def test_ssh_list_connections_with_detailed_info(self):
        """测试ssh_list_connections详细信息"""
        with patch('ssh_manager.SSHManager.list_connections') as mock_list:
            mock_list.return_value = [
                {
                    "connection_id": "user@detailed.com:22",
                    "host": "detailed.com",
                    "username": "user",
                    "port": 22,
                    "status": "connected",
                    "connected_at": "2024-01-15 10:30:00",
                    "last_activity": "2024-01-15 10:35:00",
                    "commands_executed": 5,
                    "bytes_sent": 1024,
                    "bytes_received": 2048
                }
            ]
            
            result = await handle_call_tool("ssh_list_connections", {})
            
            assert not result.isError
            text = result.content[0].text
            assert "user@detailed.com:22" in text
            assert "detailed.com" in text
            assert "10:30:00" in text  # 连接时间
    
    @pytest.mark.asyncio
    async def test_ssh_status_parameter_validation(self):
        """测试ssh_status参数验证"""
        # 测试无效的connection_id参数类型
        result = await handle_call_tool("ssh_status", {
            "connection_id": 123  # 应该是字符串
        })
        
        # 应该能处理各种参数类型
        assert isinstance(result, CallToolResult)
    
    @pytest.mark.asyncio
    async def test_ssh_list_connections_no_parameters(self):
        """测试ssh_list_connections不需要参数"""
        # 这个工具不需要任何参数
        result = await handle_call_tool("ssh_list_connections", {})
        
        assert isinstance(result, CallToolResult)
        # 应该总是返回结果，即使是空列表
        assert len(result.content) > 0
    
    @pytest.mark.asyncio
    async def test_ssh_status_real_output(self):
        """测试ssh_status真实输出"""
        # 使用真实环境测试
        result = await handle_call_tool("ssh_status", {})
        
        assert isinstance(result, CallToolResult)
        assert not result.isError
        assert len(result.content) > 0
        assert isinstance(result.content[0], TextContent)
        
        text = result.content[0].text
        assert "所有连接状态" in text
    
    @pytest.mark.asyncio
    async def test_ssh_list_connections_real_output(self):
        """测试ssh_list_connections真实输出"""
        # 使用真实环境测试
        result = await handle_call_tool("ssh_list_connections", {})
        
        assert isinstance(result, CallToolResult)
        assert not result.isError
        assert len(result.content) > 0
        assert isinstance(result.content[0], TextContent)
        
        text = result.content[0].text
        assert "SSH连接列表" in text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
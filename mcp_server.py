#!/usr/bin/env python3
import asyncio
import json
import sys
import logging
import time
import os
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool, TextContent, ImageContent, EmbeddedResource,
    CallToolRequest, CallToolResult, ReadResourceRequest, ReadResourceResult,
    ListResourcesRequest, ListResourcesResult,
    ListToolsRequest, ListToolsResult
)
from pydantic import BaseModel, Field
from ssh_manager import SSHManager
from config_loader import ConfigLoader, SSHConnectionConfig

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建配置加载器和SSH管理器实例
config_loader = ConfigLoader()
try:
    config = config_loader.load_config()
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, config.log_level.upper()))
except Exception as e:
    logger.warning(f"配置加载失败，使用默认配置: {e}")
    config = None

ssh_manager = SSHManager()

# 创建MCP服务器
server = Server("ssh-agent-mcp")

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

class SSHConnectionParams(BaseModel):
    host: str = Field(description="SSH服务器主机名或IP地址")
    username: str = Field(description="SSH用户名")
    port: int = Field(default=22, description="SSH端口，默认为22")
    password: Optional[str] = Field(default=None, description="SSH密码")
    private_key: Optional[str] = Field(default=None, description="私钥文件路径")
    private_key_password: Optional[str] = Field(default=None, description="私钥密码")

class ExecuteCommandParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    command: str = Field(description="要执行的命令")
    timeout: int = Field(default=30, description="命令超时时间（秒）")

class StartAsyncCommandParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    command: str = Field(description="要执行的长时间运行命令")

class GetCommandStatusParams(BaseModel):
    command_id: str = Field(description="异步命令ID")

class TerminateCommandParams(BaseModel):
    command_id: str = Field(description="要终止的异步命令ID")

class ConnectByNameParams(BaseModel):
    connection_name: str = Field(description="配置文件中的连接名称")

class ConnectByConfigHostParams(BaseModel):
    config_host: str = Field(description="SSH config文件中的主机名")
    username: Optional[str] = Field(default=None, description="可选用户名，覆盖config中的设置")
    password: Optional[str] = Field(default=None, description="可选密码")
    private_key: Optional[str] = Field(default=None, description="可选私钥文件路径")
    private_key_password: Optional[str] = Field(default=None, description="可选私钥密码")

class ListConfigParams(BaseModel):
    filter_tag: Optional[str] = Field(default=None, description="按标签过滤连接")

class StartInteractiveParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    command: str = Field(description="要启动的交互式命令")
    pty_width: int = Field(default=80, description="伪终端宽度")
    pty_height: int = Field(default=24, description="伪终端高度")

class SendInputParams(BaseModel):
    session_id: str = Field(description="交互式会话ID")
    input_text: str = Field(description="要发送的输入文本")

class GetInteractiveOutputParams(BaseModel):
    session_id: str = Field(description="交互式会话ID")
    max_lines: int = Field(default=50, description="最大返回行数")

class TerminateInteractiveParams(BaseModel):
    session_id: str = Field(description="要终止的交互式会话ID")

class UploadFileParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    local_path: str = Field(description="本地文件路径")
    remote_path: str = Field(description="远程文件路径")

class DownloadFileParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    remote_path: str = Field(description="远程文件路径")
    local_path: str = Field(description="本地文件路径")

class ListRemoteDirectoryParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    remote_path: str = Field(default=".", description="远程目录路径，默认为当前目录")

class CreateRemoteDirectoryParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    remote_path: str = Field(description="要创建的远程目录路径")
    mode: int = Field(default=0o755, description="目录权限，默认为755")
    parents: bool = Field(default=True, description="是否递归创建父目录，默认为True")

class RemoveRemoteFileParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    remote_path: str = Field(description="要删除的远程文件或目录路径")

class GetRemoteFileInfoParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    remote_path: str = Field(description="远程文件或目录路径")

class RenameRemotePathParams(BaseModel):
    connection_id: str = Field(description="SSH连接ID")
    old_path: str = Field(description="原始路径")
    new_path: str = Field(description="新路径")

class CleanupCommandsParams(BaseModel):
    max_age: int = Field(default=3600, description="保留时间（秒），默认3600秒")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """列出可用的工具"""
    return [
        Tool(
            name="ssh_connect",
            description="建立SSH连接",
            inputSchema={
                "type": "object",
                "properties": {
                    "host": {"type": "string", "description": "SSH服务器主机名或IP地址"},
                    "username": {"type": "string", "description": "SSH用户名"},
                    "port": {"type": "integer", "description": "SSH端口", "default": 22},
                    "password": {"type": "string", "description": "SSH密码"},
                    "private_key": {"type": "string", "description": "私钥文件路径"},
                    "private_key_password": {"type": "string", "description": "私钥密码"}
                },
                "required": ["host", "username"]
            }
        ),
        Tool(
            name="ssh_disconnect",
            description="断开SSH连接",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"}
                },
                "required": ["connection_id"]
            }
        ),
        Tool(
            name="ssh_status",
            description="查询SSH连接状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID（可选）"}
                }
            }
        ),
        Tool(
            name="ssh_list_connections",
            description="列出所有SSH连接",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ssh_execute",
            description="在SSH连接上执行命令",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "command": {"type": "string", "description": "要执行的命令"},
                    "timeout": {"type": "integer", "description": "命令超时时间（秒）", "default": 30}
                },
                "required": ["connection_id", "command"]
            }
        ),
        Tool(
            name="ssh_disconnect_all",
            description="断开所有SSH连接",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ssh_start_async_command",
            description="启动长时间运行的异步命令",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "command": {"type": "string", "description": "要执行的长时间运行命令"}
                },
                "required": ["connection_id", "command"]
            }
        ),
        Tool(
            name="ssh_get_command_status",
            description="获取异步命令状态和最新输出",
            inputSchema={
                "type": "object",
                "properties": {
                    "command_id": {"type": "string", "description": "异步命令ID"}
                },
                "required": ["command_id"]
            }
        ),
        Tool(
            name="ssh_list_async_commands",
            description="列出所有异步命令状态",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ssh_terminate_command",
            description="终止正在运行的异步命令",
            inputSchema={
                "type": "object",
                "properties": {
                    "command_id": {"type": "string", "description": "要终止的异步命令ID"}
                },
                "required": ["command_id"]
            }
        ),
        Tool(
            name="ssh_cleanup_commands",
            description="清理已完成的异步命令",
            inputSchema={
                "type": "object",
                "properties": {
                    "max_age": {"type": "integer", "description": "保留时间（秒），默认3600秒"}
                }
            }
        ),
        Tool(
            name="ssh_connect_by_name",
            description="使用配置文件中的连接名称建立SSH连接",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_name": {"type": "string", "description": "配置文件中的连接名称"}
                },
                "required": ["connection_name"]
            }
        ),
        Tool(
            name="ssh_list_config",
            description="列出配置文件中的所有SSH连接",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_tag": {"type": "string", "description": "按标签过滤连接（可选）"}
                }
            }
        ),
        Tool(
            name="ssh_auto_connect",
            description="自动连接配置文件中标记为auto_connect的连接",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ssh_start_interactive",
            description="启动交互式SSH会话（支持sudo、vim、mysql等需要交互输入的命令）",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "command": {"type": "string", "description": "要启动的交互式命令"},
                    "pty_width": {"type": "integer", "description": "伪终端宽度", "default": 80},
                    "pty_height": {"type": "integer", "description": "伪终端高度", "default": 24}
                },
                "required": ["connection_id", "command"]
            }
        ),
        Tool(
            name="ssh_send_input",
            description="向交互式会话发送输入（如密码、命令等）",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "交互式会话ID"},
                    "input_text": {"type": "string", "description": "要发送的输入文本"}
                },
                "required": ["session_id", "input_text"]
            }
        ),
        Tool(
            name="ssh_get_interactive_output",
            description="获取交互式会话的输出",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "交互式会话ID"},
                    "max_lines": {"type": "integer", "description": "最大返回行数", "default": 50}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="ssh_list_interactive_sessions",
            description="列出所有活跃的交互式会话",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="ssh_terminate_interactive",
            description="终止交互式会话",
            inputSchema={
                "type": "object",
                "properties": {
                    "session_id": {"type": "string", "description": "要终止的交互式会话ID"}
                },
                "required": ["session_id"]
            }
        ),
        Tool(
            name="ssh_connect_by_config_host",
            description="使用SSH config文件中的主机名建立连接",
            inputSchema={
                "type": "object",
                "properties": {
                    "config_host": {"type": "string", "description": "SSH config文件中的主机名"},
                    "username": {"type": "string", "description": "可选用户名，覆盖config中的设置"},
                    "password": {"type": "string", "description": "可选密码"},
                    "private_key": {"type": "string", "description": "可选私钥文件路径"},
                    "private_key_password": {"type": "string", "description": "可选私钥密码"}
                },
                "required": ["config_host"]
            }
        ),
        Tool(
            name="ssh_upload_file",
            description="上传文件到远程服务器",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "local_path": {"type": "string", "description": "本地文件路径"},
                    "remote_path": {"type": "string", "description": "远程文件路径"}
                },
                "required": ["connection_id", "local_path", "remote_path"]
            }
        ),
        Tool(
            name="ssh_download_file",
            description="从远程服务器下载文件",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "remote_path": {"type": "string", "description": "远程文件路径"},
                    "local_path": {"type": "string", "description": "本地文件路径"}
                },
                "required": ["connection_id", "remote_path", "local_path"]
            }
        ),
        Tool(
            name="ssh_list_remote_directory",
            description="列出远程目录内容",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "remote_path": {"type": "string", "description": "远程目录路径", "default": "."}
                },
                "required": ["connection_id"]
            }
        ),
        Tool(
            name="ssh_create_remote_directory",
            description="在远程服务器上创建目录",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "remote_path": {"type": "string", "description": "要创建的远程目录路径"},
                    "mode": {"type": "integer", "description": "目录权限", "default": 493},
                    "parents": {"type": "boolean", "description": "是否递归创建父目录", "default": True}
                },
                "required": ["connection_id", "remote_path"]
            }
        ),
        Tool(
            name="ssh_remove_remote_file",
            description="删除远程文件或目录",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "remote_path": {"type": "string", "description": "要删除的远程文件或目录路径"}
                },
                "required": ["connection_id", "remote_path"]
            }
        ),
        Tool(
            name="ssh_get_remote_file_info",
            description="获取远程文件或目录信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "remote_path": {"type": "string", "description": "远程文件或目录路径"}
                },
                "required": ["connection_id", "remote_path"]
            }
        ),
        Tool(
            name="ssh_rename_remote_path",
            description="重命名远程文件或目录",
            inputSchema={
                "type": "object",
                "properties": {
                    "connection_id": {"type": "string", "description": "SSH连接ID"},
                    "old_path": {"type": "string", "description": "原始路径"},
                    "new_path": {"type": "string", "description": "新路径"}
                },
                "required": ["connection_id", "old_path", "new_path"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """处理工具调用"""
    try:
        if name == "ssh_connect":
            params = SSHConnectionParams(**arguments)
            connection_id = await ssh_manager.create_connection(
                host=params.host,
                username=params.username,
                port=params.port,
                password=params.password,
                private_key=params.private_key,
                private_key_password=params.private_key_password
            )
            
            # 检查连接状态
            status = await ssh_manager.get_connection_status(connection_id)
            
            if status["status"] == "connected":
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"SSH连接建立成功\n连接ID: {connection_id}\n主机: {params.username}@{params.host}:{params.port}"
                        )
                    ],
                    isError=False
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"SSH连接失败\n连接ID: {connection_id}\n主机: {params.username}@{params.host}:{params.port}\n错误信息: {status.get('error_message', '未知错误')}"
                        )
                    ],
                    isError=True
                )
            
        elif name == "ssh_disconnect":
            if "connection_id" not in arguments:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="缺少必需参数: connection_id (SSH连接ID)"
                    )],
                    isError=True
                )
            connection_id = arguments["connection_id"]
            success = await ssh_manager.disconnect(connection_id)
            
            if success:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"SSH连接已断开: {connection_id}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"断开连接失败: 连接ID {connection_id} 不存在"
                    )],
                    isError=True
                )
                
        elif name == "ssh_status":
            connection_id = arguments.get("connection_id")
            
            if connection_id:
                status = await ssh_manager.get_connection_status(connection_id)
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"连接状态:\n{json.dumps(status, indent=2, ensure_ascii=False)}"
                    )]
                )
            else:
                connections = await ssh_manager.list_connections()
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"所有连接状态:\n{json.dumps(connections, indent=2, ensure_ascii=False)}"
                    )]
                )
                
        elif name == "ssh_list_connections":
            connections = await ssh_manager.list_connections()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"SSH连接列表:\n{json.dumps(connections, indent=2, ensure_ascii=False)}"
                )]
            )
            
        elif name == "ssh_execute":
            params = ExecuteCommandParams(**arguments)
            result = await ssh_manager.execute_command(
                connection_id=params.connection_id,
                command=params.command,
                timeout=params.timeout
            )
            
            output = f"命令执行结果:\n"
            output += f"连接ID: {params.connection_id}\n"
            output += f"命令: {params.command}\n"
            output += f"成功: {result['success']}\n"
            output += f"退出码: {result['exit_code']}\n"
            output += f"标准输出:\n{result['stdout']}\n"
            if result['stderr']:
                output += f"标准错误:\n{result['stderr']}\n"
                
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=output
                )],
                isError=not result['success']
            )
            
        elif name == "ssh_disconnect_all":
            await ssh_manager.disconnect_all()
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text="所有SSH连接已断开"
                )]
            )
            
        elif name == "ssh_start_async_command":
            params = StartAsyncCommandParams(**arguments)
            try:
                command_id = await ssh_manager.start_async_command(
                    connection_id=params.connection_id,
                    command=params.command
                )
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"异步命令已启动\n命令ID: {command_id}\n连接ID: {params.connection_id}\n命令: {params.command}\n\n使用 ssh_get_command_status 工具查询命令状态和输出"
                    )]
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"启动异步命令失败: {str(e)}"
                    )],
                    isError=True
                )
                
        elif name == "ssh_get_command_status":
            params = GetCommandStatusParams(**arguments)
            status = await ssh_manager.get_command_status(params.command_id)
            
            if status.get("status") == "not_found":
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"命令不存在: {params.command_id}"
                    )],
                    isError=True
                )
            
            output = f"异步命令状态:\n"
            output += f"命令ID: {status['command_id']}\n"
            output += f"连接ID: {status['connection_id']}\n"
            output += f"命令: {status['command']}\n"
            output += f"状态: {status['status']}\n"
            output += f"开始时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(status['start_time']))}\n"
            if status['end_time']:
                output += f"结束时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(status['end_time']))}\n"
            output += f"运行时长: {status['duration']:.2f}秒\n"
            if status['exit_code'] is not None:
                output += f"退出码: {status['exit_code']}\n"
            output += f"标准输出大小: {status['stdout_size']} 字节\n"
            output += f"标准错误大小: {status['stderr_size']} 字节\n"
            
            if status['stdout']:
                output += f"\n标准输出:\n{status['stdout']}\n"
            if status['stderr']:
                output += f"\n标准错误:\n{status['stderr']}\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=output
                )],
                isError=status['status'] in ['failed', 'terminated']
            )
            
        elif name == "ssh_list_async_commands":
            commands = await ssh_manager.list_async_commands()
            
            if not commands:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="当前没有异步命令在运行"
                    )]
                )
            
            output = f"异步命令列表 (共 {len(commands)} 个):\n\n"
            for cmd_id, cmd_info in commands.items():
                output += f"命令ID: {cmd_id}\n"
                output += f"  连接ID: {cmd_info['connection_id']}\n"
                output += f"  命令: {cmd_info['command']}\n"
                output += f"  状态: {cmd_info['status']}\n"
                output += f"  运行时长: {cmd_info['duration']:.2f}秒\n"
                if cmd_info['exit_code'] is not None:
                    output += f"  退出码: {cmd_info['exit_code']}\n"
                output += f"  输出大小: stdout={cmd_info['stdout_size']} bytes, stderr={cmd_info['stderr_size']} bytes\n"
                output += "\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=output
                )]
            )
            
        elif name == "ssh_terminate_command":
            params = TerminateCommandParams(**arguments)
            success = await ssh_manager.terminate_command(params.command_id)
            
            if success:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"命令已终止: {params.command_id}"
                    )]
                )
            else:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"终止命令失败: {params.command_id} (命令不存在或无法终止)"
                    )],
                    isError=True
                )
                
        elif name == "ssh_cleanup_commands":
            params = CleanupCommandsParams(**arguments)
            cleaned_count = await ssh_manager.cleanup_completed_commands(params.max_age)
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"已清理 {cleaned_count} 个完成的命令 (保留时间: {params.max_age}秒)"
                )]
            )
            
        elif name == "ssh_connect_by_name":
            params = ConnectByNameParams(**arguments)
            
            if not config:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="配置文件未加载，无法使用名称连接"
                    )],
                    isError=True
                )
            
            conn_config = config_loader.get_connection_by_name(params.connection_name)
            if not conn_config:
                available_names = config_loader.list_connection_names()
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"连接名称 '{params.connection_name}' 不存在\n可用连接名称: {', '.join(available_names)}"
                    )],
                    isError=True
                )
            
            connection_id = await ssh_manager.create_connection(
                host=conn_config.host,
                username=conn_config.username,
                port=conn_config.port,
                password=conn_config.password,
                private_key=conn_config.private_key,
                private_key_password=conn_config.private_key_password
            )
            
            # 检查连接状态
            status = await ssh_manager.get_connection_status(connection_id)
            
            output = f"使用配置连接: {params.connection_name}\n"
            output += f"连接ID: {connection_id}\n"
            output += f"主机: {conn_config.username}@{conn_config.host}:{conn_config.port}\n"
            if conn_config.description:
                output += f"描述: {conn_config.description}\n"
            if conn_config.tags:
                output += f"标签: {', '.join(conn_config.tags)}\n"
            
            if status["status"] == "connected":
                output += f"状态: 连接成功"
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )],
                    isError=False
                )
            else:
                output += f"状态: 连接失败\n"
                output += f"错误信息: {status.get('error_message', '未知错误')}"
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )],
                    isError=True
                )
                
        elif name == "ssh_list_config":
            params = ListConfigParams(**arguments)
            
            if not config:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="配置文件未加载"
                    )],
                    isError=True
                )
            
            if params.filter_tag:
                connections = config_loader.get_connections_by_tag(params.filter_tag)
                title = f"配置文件中的SSH连接 (标签: {params.filter_tag})"
            else:
                connections = config.connections
                title = "配置文件中的所有SSH连接"
            
            if not connections:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="没有找到匹配的连接配置"
                    )]
                )
            
            output = f"{title} (共 {len(connections)} 个):\n\n"
            for conn in connections:
                output += f"名称: {conn.name}\n"
                output += f"  主机: {conn.username}@{conn.host}:{conn.port}\n"
                if conn.description:
                    output += f"  描述: {conn.description}\n"
                if conn.tags:
                    output += f"  标签: {', '.join(conn.tags)}\n"
                output += f"  认证方式: {'私钥' if conn.private_key else '密码' if conn.password else '未配置'}\n"
                output += "\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=output
                )]
            )
            
        elif name == "ssh_auto_connect":
            if not config:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="配置文件未加载，无法自动连接"
                    )],
                    isError=True
                )
            
            if not config.auto_connect:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text="配置文件中没有设置自动连接的连接"
                    )]
                )
            
            results = []
            errors = []
            
            for conn_name in config.auto_connect:
                conn_config = config_loader.get_connection_by_name(conn_name)
                if not conn_config:
                    errors.append(f"连接名称 '{conn_name}' 不存在")
                    continue
                
                connection_id = await ssh_manager.create_connection(
                    host=conn_config.host,
                    username=conn_config.username,
                    port=conn_config.port,
                    password=conn_config.password,
                    private_key=conn_config.private_key,
                    private_key_password=conn_config.private_key_password
                )
                
                # 检查连接状态
                status = await ssh_manager.get_connection_status(connection_id)
                if status["status"] == "connected":
                    results.append(f"{conn_name} -> {connection_id}")
                else:
                    error_msg = status.get('error_message', '未知错误')
                    errors.append(f"{conn_name}: {error_msg}")
            
            output = f"自动连接完成\n\n"
            output += f"成功连接 ({len(results)} 个):\n"
            for result in results:
                output += f"  {result}\n"
            
            if errors:
                output += f"\n连接失败 ({len(errors)} 个):\n"
                for error in errors:
                    output += f"  {error}\n"
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=output
                )],
                isError=len(errors) > 0 and len(results) == 0
            )
            
        elif name == "ssh_start_interactive":
            params = StartInteractiveParams(**arguments)
            try:
                session_id = await ssh_manager.start_interactive_session(
                    connection_id=params.connection_id,
                    command=params.command,
                    pty_width=params.pty_width,
                    pty_height=params.pty_height
                )
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"交互式会话已启动\n会话ID: {session_id}\n连接ID: {params.connection_id}\n命令: {params.command}\n\n使用 ssh_get_interactive_output 获取输出\n使用 ssh_send_input 发送输入"
                    )]
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"启动交互式会话失败: {str(e)}"
                    )],
                    isError=True
                )
                
        elif name == "ssh_send_input":
            params = SendInputParams(**arguments)
            try:
                success = await ssh_manager.send_input_to_session(
                    session_id=params.session_id,
                    input_text=params.input_text
                )
                
                if success:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"输入已发送到会话 {params.session_id}\n输入内容: {params.input_text}"
                        )]
                    )
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"发送输入失败: 会话 {params.session_id} 不存在或已关闭"
                        )],
                        isError=True
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"发送输入失败: {str(e)}"
                    )],
                    isError=True
                )
                
        elif name == "ssh_get_interactive_output":
            params = GetInteractiveOutputParams(**arguments)
            try:
                output_data = await ssh_manager.get_interactive_output(
                    session_id=params.session_id,
                    max_lines=params.max_lines
                )
                
                if output_data is None:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"会话 {params.session_id} 不存在"
                        )],
                        isError=True
                    )
                
                output = f"交互式会话输出 (会话ID: {params.session_id})\n"
                output += f"状态: {output_data['status']}\n"
                output += f"输出行数: {len(output_data['output'].splitlines()) if output_data['output'] else 0}\n"
                output += f"缓冲区大小: {output_data['output_size']}\n\n"
                
                if output_data['output']:
                    output += "输出内容:\n"
                    output += "\n".join(output_data['output'])
                else:
                    output += "暂无输出"
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )]
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"获取输出失败: {str(e)}"
                    )],
                    isError=True
                )
                
        elif name == "ssh_list_interactive_sessions":
            try:
                sessions = await ssh_manager.list_interactive_sessions()
                
                if not sessions:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text="当前没有活跃的交互式会话"
                        )]
                    )
                
                output = f"活跃的交互式会话 ({len(sessions)} 个):\n\n"
                for session_id, session_info in sessions.items():
                    output += f"会话ID: {session_id}\n"
                    output += f"  连接ID: {session_info['connection_id']}\n"
                    output += f"  命令: {session_info['command']}\n"
                    output += f"  状态: {session_info['status']}\n"
                    output += f"  启动时间: {session_info['start_time']}\n"
                    output += f"  缓冲区大小: {session_info['buffer_size']}\n\n"
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )]
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"列出交互式会话失败: {str(e)}"
                    )],
                    isError=True
                )
                
        elif name == "ssh_terminate_interactive":
            params = TerminateInteractiveParams(**arguments)
            try:
                success = await ssh_manager.terminate_interactive_session(params.session_id)
                
                if success:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"交互式会话 {params.session_id} 已终止"
                        )]
                    )
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"终止会话失败: 会话 {params.session_id} 不存在"
                        )],
                        isError=True
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"终止会话失败: {str(e)}"
                    )],
                    isError=True
                )
            
        elif name == "ssh_connect_by_config_host":
            params = ConnectByConfigHostParams(**arguments)
            try:
                connection_id = await ssh_manager.create_connection_from_config(
                    config_host=params.config_host,
                    username=params.username,
                    password=params.password,
                    private_key=params.private_key,
                    private_key_password=params.private_key_password
                )
                
                # 检查连接状态
                status = await ssh_manager.get_connection_status(connection_id)
                
                output = f"使用SSH config连接: {params.config_host}\n"
                output += f"连接ID: {connection_id}\n"
                
                if status["status"] == "connected":
                    output += f"状态: 连接成功\n"
                    output += f"实际主机: {status['host']}:{status['port']}\n"
                    output += f"用户名: {status['username']}"
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=output
                        )],
                        isError=False
                    )
                else:
                    output += f"状态: 连接失败\n"
                    output += f"错误信息: {status.get('error_message', '未知错误')}"
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=output
                        )],
                        isError=True
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"SSH config连接失败: {str(e)}"
                    )],
                    isError=True
                )
            
        # SFTP 工具处理
        elif name == "ssh_upload_file":
            params = UploadFileParams(**arguments)
            try:
                result = await ssh_manager.upload_file(
                    connection_id=params.connection_id,
                    local_path=params.local_path,
                    remote_path=params.remote_path
                )
                
                output = f"文件上传操作结果:\n"
                output += f"连接ID: {params.connection_id}\n"
                output += f"本地路径: {params.local_path}\n"
                output += f"远程路径: {params.remote_path}\n"
                output += f"成功: {result['success']}\n"
                
                if result['success']:
                    output += f"本地大小: {result['local_size']} 字节\n"
                    output += f"远程大小: {result['remote_size']} 字节\n"
                    if 'warning' in result:
                        output += f"警告: {result['warning']}\n"
                    output += f"消息: {result['message']}\n"
                else:
                    output += f"错误: {result['error']}\n"
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )],
                    isError=not result['success']
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"上传文件失败: {str(e)}"
                    )],
                    isError=True
                )
        
        elif name == "ssh_download_file":
            params = DownloadFileParams(**arguments)
            try:
                result = await ssh_manager.download_file(
                    connection_id=params.connection_id,
                    remote_path=params.remote_path,
                    local_path=params.local_path
                )
                
                output = f"文件下载操作结果:\n"
                output += f"连接ID: {params.connection_id}\n"
                output += f"远程路径: {params.remote_path}\n"
                output += f"本地路径: {params.local_path}\n"
                output += f"成功: {result['success']}\n"
                
                if result['success']:
                    output += f"远程大小: {result['remote_size']} 字节\n"
                    output += f"本地大小: {result['local_size']} 字节\n"
                    if 'warning' in result:
                        output += f"警告: {result['warning']}\n"
                    output += f"消息: {result['message']}\n"
                else:
                    output += f"错误: {result['error']}\n"
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )],
                    isError=not result['success']
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"下载文件失败: {str(e)}"
                    )],
                    isError=True
                )
        
        elif name == "ssh_list_remote_directory":
            params = ListRemoteDirectoryParams(**arguments)
            try:
                result = await ssh_manager.list_remote_directory(
                    connection_id=params.connection_id,
                    remote_path=params.remote_path
                )
                
                if result['success']:
                    output = f"远程目录列表:\n"
                    output += f"连接ID: {params.connection_id}\n"
                    output += f"路径: {result['path']}\n"
                    output += f"总项目数: {result['total_count']}\n"
                    output += f"目录数: {result['directory_count']}\n"
                    output += f"文件数: {result['file_count']}\n\n"
                    
                    if result['directories']:
                        output += "目录:\n"
                        for directory in result['directories']:
                            output += f"  📁 {directory['name']}/ (权限: {directory['permissions']}, 所有者: {directory['owner']})\n"
                        output += "\n"
                    
                    if result['files']:
                        output += "文件:\n"
                        for file in result['files']:
                            size_str = _format_file_size(file['size'])
                            modified_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file['modified']))
                            output += f"  📄 {file['name']} (大小: {size_str}, 权限: {file['permissions']}, 修改时间: {modified_time})\n"
                    
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=output
                        )]
                    )
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"列出远程目录失败: {result['error']}"
                        )],
                        isError=True
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"列出远程目录失败: {str(e)}"
                    )],
                    isError=True
                )
        
        elif name == "ssh_create_remote_directory":
            params = CreateRemoteDirectoryParams(**arguments)
            try:
                result = await ssh_manager.create_remote_directory(
                    connection_id=params.connection_id,
                    remote_path=params.remote_path,
                    mode=params.mode,
                    parents=params.parents
                )
                
                output = f"创建远程目录结果:\n"
                output += f"连接ID: {params.connection_id}\n"
                output += f"路径: {params.remote_path}\n"
                output += f"成功: {result['success']}\n"
                
                if result['success']:
                    output += f"权限: {result['mode']}\n"
                    output += f"消息: {result['message']}\n"
                else:
                    output += f"错误: {result['error']}\n"
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )],
                    isError=not result['success']
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"创建远程目录失败: {str(e)}"
                    )],
                    isError=True
                )
        
        elif name == "ssh_remove_remote_file":
            params = RemoveRemoteFileParams(**arguments)
            try:
                result = await ssh_manager.remove_remote_file(
                    connection_id=params.connection_id,
                    remote_path=params.remote_path
                )
                
                output = f"删除远程文件/目录结果:\n"
                output += f"连接ID: {params.connection_id}\n"
                output += f"路径: {params.remote_path}\n"
                output += f"成功: {result['success']}\n"
                
                if result['success']:
                    output += f"类型: {result['type']}\n"
                    output += f"消息: {result['message']}\n"
                else:
                    output += f"错误: {result['error']}\n"
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )],
                    isError=not result['success']
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"删除远程文件失败: {str(e)}"
                    )],
                    isError=True
                )
        
        elif name == "ssh_get_remote_file_info":
            params = GetRemoteFileInfoParams(**arguments)
            try:
                result = await ssh_manager.get_remote_file_info(
                    connection_id=params.connection_id,
                    remote_path=params.remote_path
                )
                
                if result['success']:
                    output = f"远程文件信息:\n"
                    output += f"连接ID: {params.connection_id}\n"
                    output += f"路径: {result['path']}\n"
                    output += f"类型: {'目录' if result['is_directory'] else '文件'}\n"
                    output += f"大小: {_format_file_size(result['size'])}\n"
                    output += f"权限: {result['permissions']}\n"
                    output += f"所有者: {result['owner']}\n"
                    output += f"组: {result['group']}\n"
                    output += f"修改时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result['modified']))}\n"
                    output += f"访问时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result['accessed']))}\n"
                    
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=output
                        )]
                    )
                else:
                    return CallToolResult(
                        content=[TextContent(
                            type="text",
                            text=f"获取远程文件信息失败: {result['error']}"
                        )],
                        isError=True
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"获取远程文件信息失败: {str(e)}"
                    )],
                    isError=True
                )
        
        elif name == "ssh_rename_remote_path":
            params = RenameRemotePathParams(**arguments)
            try:
                result = await ssh_manager.rename_remote_path(
                    connection_id=params.connection_id,
                    old_path=params.old_path,
                    new_path=params.new_path
                )
                
                output = f"重命名远程路径结果:\n"
                output += f"连接ID: {params.connection_id}\n"
                output += f"原路径: {params.old_path}\n"
                output += f"新路径: {params.new_path}\n"
                output += f"成功: {result['success']}\n"
                
                if result['success']:
                    output += f"消息: {result['message']}\n"
                else:
                    output += f"错误: {result['error']}\n"
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=output
                    )],
                    isError=not result['success']
                )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=f"重命名远程路径失败: {str(e)}"
                    )],
                    isError=True
                )
            
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=f"未知工具: {name}"
                )],
                isError=True
            )
            
    except Exception as e:
        logger.error(f"工具调用失败: {e}")
        error_message = str(e)
        
        # 改进错误消息的可读性
        if "validation error for" in error_message:
            # Pydantic 验证错误，提取更友好的信息
            if "Field required" in error_message:
                # 收集所有缺失的字段
                missing_fields = []
                if "connection_id" in error_message:
                    missing_fields.append("connection_id (SSH连接ID)")
                if "command" in error_message:
                    missing_fields.append("command (要执行的命令)")
                if "session_id" in error_message:
                    missing_fields.append("session_id (交互式会话ID)")
                if "command_id" in error_message:
                    missing_fields.append("command_id (异步命令ID)")
                if "remote_path" in error_message:
                    missing_fields.append("remote_path (远程文件路径)")
                if "local_path" in error_message:
                    missing_fields.append("local_path (本地文件路径)")
                if "old_path" in error_message:
                    missing_fields.append("old_path (原始路径)")
                if "new_path" in error_message:
                    missing_fields.append("new_path (新路径)")
                if "host" in error_message:
                    missing_fields.append("host (SSH服务器地址)")
                if "username" in error_message:
                    missing_fields.append("username (用户名)")
                if "config_host" in error_message:
                    missing_fields.append("config_host (SSH config主机名)")
                if "connection_name" in error_message:
                    missing_fields.append("connection_name (连接名称)")
                if "input_text" in error_message:
                    missing_fields.append("input_text (输入文本)")
                
                if missing_fields:
                    if len(missing_fields) == 1:
                        error_message = f"缺少必需参数: {missing_fields[0]}"
                    else:
                        error_message = f"缺少必需参数: {', '.join(missing_fields)}"
                else:
                    error_message = "缺少必需参数，请检查输入"
            elif "extra fields not permitted" in error_message:
                error_message = "参数错误: 包含不允许的额外字段"
            else:
                error_message = f"参数验证失败: {error_message}"
        
        return CallToolResult(
            content=[TextContent(
                type="text",
                text=error_message
            )],
            isError=True
        )

async def main():
    """主函数"""
    try:
        # 启动连接健康检查
        await ssh_manager.start_health_check()
        
        # 启动keep-alive
        await ssh_manager.start_keepalive()
        
        # 使用stdio服务器
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="ssh-agent-mcp",
                    server_version="1.0.0",
                    capabilities={
                        "tools": {},
                    },
                ),
            )
    finally:
        # 确保清理资源
        await ssh_manager.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
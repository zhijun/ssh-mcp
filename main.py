#!/usr/bin/env python3
import asyncio
import sys
import logging
import argparse
import os
from pathlib import Path
from typing import Optional
from mcp_server import main as mcp_main
from ssh_manager import SSHManager
from config_loader import ConfigLoader

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="SSH Agent MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 使用命令行参数
  uvx ssh-agent-mcp --host=192.168.1.100 --user=root --password=mypass
  
  # 使用配置文件
  uvx ssh-agent-mcp --config=/path/to/ssh_config.json --connection=production
  
  # 混合使用（配置文件 + 命令行覆盖）
  uvx ssh-agent-mcp --config=ssh_config.json --host=192.168.1.100
        """
    )
    
    # 基本参数
    parser.add_argument("--host", help="SSH服务器主机名或IP地址")
    parser.add_argument("--port", type=int, default=22, help="SSH端口，默认为22")
    parser.add_argument("--user", "--username", help="SSH用户名")
    parser.add_argument("--password", help="SSH密码")
    parser.add_argument("--key", "--private-key", help="私钥文件路径")
    parser.add_argument("--key-password", "--private-key-password", help="私钥密码")
    
    # 配置文件参数
    parser.add_argument("--config", "-c", help="SSH配置文件路径")
    parser.add_argument("--connection", help="配置文件中的连接名称")
    
    # 服务器参数
    parser.add_argument("--timeout", type=int, default=30000, help="命令超时时间（毫秒），默认30000")
    parser.add_argument("--max-chars", type=str, default="none", help="最大输出字符数，默认none")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO", help="日志级别")
    
    # 自动连接
    parser.add_argument("--auto-connect", action="store_true", help="启动时自动连接")
    
    return parser.parse_args()

class SSHConnectionConfig:
    """SSH连接配置类"""
    def __init__(self, host: str, username: str, port: int = 22, 
                 password: Optional[str] = None, private_key: Optional[str] = None,
                 private_key_password: Optional[str] = None):
        self.host = host
        self.username = username
        self.port = port
        self.password = password
        self.private_key = private_key
        self.private_key_password = private_key_password

def load_connection_from_config(config_path: str, connection_name: str) -> Optional[SSHConnectionConfig]:
    """从配置文件加载连接配置"""
    try:
        config_loader = ConfigLoader(config_path)
        config = config_loader.load_config()
        
        conn_config = config_loader.get_connection_by_name(connection_name)
        if not conn_config:
            print(f"错误: 连接名称 '{connection_name}' 在配置文件中不存在")
            return None
        
        return SSHConnectionConfig(
            host=conn_config.host,
            username=conn_config.username,
            port=conn_config.port,
            password=conn_config.password,
            private_key=conn_config.private_key,
            private_key_password=conn_config.private_key_password
        )
    except Exception as e:
        print(f"错误: 加载配置文件失败: {e}")
        return None

def validate_connection_config(args) -> Optional[SSHConnectionConfig]:
    """验证并创建连接配置（可选）"""
    # 如果指定了配置文件和连接名称，从配置文件加载
    if args.config and args.connection:
        config = load_connection_from_config(args.config, args.connection)
        if not config:
            return None
        
        # 命令行参数可以覆盖配置文件中的设置
        if args.host:
            config.host = args.host
        if args.user:
            config.username = args.user
        if args.port != 22:
            config.port = args.port
        if args.password:
            config.password = args.password
        if args.key:
            config.private_key = args.key
        if args.key_password:
            config.private_key_password = args.key_password
        
        return config
    
    # 直接使用命令行参数
    if args.host and args.user:
        return SSHConnectionConfig(
            host=args.host,
            username=args.user,
            port=args.port,
            password=args.password,
            private_key=args.key,
            private_key_password=args.key_password
        )
    
    # 如果只指定了配置文件，但没有指定连接名称，列出可用连接
    if args.config and not args.connection:
        try:
            config_loader = ConfigLoader(args.config)
            config = config_loader.load_config()
            print("可用的连接:")
            for conn in config.connections:
                print(f"  - {conn.name} ({conn.username}@{conn.host}:{conn.port})")
            print("\n请使用 --connection 参数指定连接名称")
        except Exception as e:
            print(f"错误: 无法读取配置文件: {e}")
        return None
    
    # 没有提供连接配置是允许的，MCP服务将等待大模型提供参数
    return None

async def setup_auto_connection(ssh_manager: SSHManager, config: SSHConnectionConfig):
    """设置自动连接"""
    try:
        connection_id = await ssh_manager.create_connection(
            host=config.host,
            username=config.username,
            port=config.port,
            password=config.password,
            private_key=config.private_key,
            private_key_password=config.private_key_password
        )
        print(f"自动连接成功: {connection_id}")
    except Exception as e:
        print(f"自动连接失败: {e}")

async def main():
    """主函数"""
    args = parse_arguments()
    
    # 设置日志级别
    logging.basicConfig(level=getattr(logging, args.log_level))
    logger = logging.getLogger(__name__)
    
    # 验证连接配置（可选）
    connection_config = validate_connection_config(args)
    
    # 如果提供了连接配置，设置环境变量供MCP服务器使用
    if connection_config:
        os.environ['SSH_HOST'] = connection_config.host
        os.environ['SSH_USERNAME'] = connection_config.username
        os.environ['SSH_PORT'] = str(connection_config.port)
        if connection_config.password:
            os.environ['SSH_PASSWORD'] = connection_config.password
        if connection_config.private_key:
            os.environ['SSH_PRIVATE_KEY'] = connection_config.private_key
        if connection_config.private_key_password:
            os.environ['SSH_PRIVATE_KEY_PASSWORD'] = connection_config.private_key_password
        
        logger.info(f"已配置SSH连接: {connection_config.username}@{connection_config.host}:{connection_config.port}")
        
        # 如果设置了自动连接，先建立连接
        if args.auto_connect:
            from ssh_manager import SSHManager
            ssh_mgr = SSHManager()
            await setup_auto_connection(ssh_mgr, connection_config)
    else:
        logger.info("未提供SSH连接配置，MCP服务将等待大模型提供连接参数")
    
    # 设置其他环境变量
    os.environ['SSH_TIMEOUT'] = str(args.timeout)
    os.environ['SSH_MAX_CHARS'] = args.max_chars
    
    try:
        # 启动MCP服务器
        logger.info("启动SSH Agent MCP服务器...")
        await mcp_main()
    except KeyboardInterrupt:
        logger.info("SSH Agent MCP服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)

# 新增：同步入口函数，供 console_scripts 调用
def cli():
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())


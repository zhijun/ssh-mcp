#!/usr/bin/env python3
"""
SSH Agent MCP 服务安装脚本
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path

def create_example_config():
    """创建示例配置文件"""
    config_path = Path.cwd() / "ssh_config.json"
    
    if config_path.exists():
        response = input(f"配置文件 {config_path} 已存在，是否覆盖？(y/N): ")
        if response.lower() != 'y':
            print("跳过配置文件创建")
            return
    
    example_config = {
        "connections": [
            {
                "name": "production-server",
                "host": "prod.example.com",
                "username": "admin",
                "port": 22,
                "private_key": str(Path.home() / ".ssh" / "id_rsa"),
                "description": "生产环境服务器",
                "tags": ["production", "critical"]
            },
            {
                "name": "development-server",
                "host": "192.168.1.100",
                "username": "dev",
                "port": 22,
                "password": "your_dev_password",
                "description": "开发环境服务器",
                "tags": ["development", "test"]
            }
        ],
        "default_timeout": 30,
        "log_level": "INFO",
        "auto_connect": ["production-server"],
        "max_connections": 10
    }
    
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
        print(f"✅ 示例配置文件已创建: {config_path}")
        print("⚠️  请编辑配置文件，修改为您的实际SSH连接信息")
    except Exception as e:
        print(f"❌ 创建配置文件失败: {e}")

def install_dependencies():
    """安装依赖"""
    print("📦 安装依赖包...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        print("✅ 依赖安装成功")
    except subprocess.CalledProcessError as e:
        print(f"❌ 依赖安装失败: {e}")
        sys.exit(1)

def create_mcp_client_config():
    """创建MCP客户端配置文件"""
    mcp_config_dir = Path.home() / ".config" / "claude-desktop"
    mcp_config_file = mcp_config_dir / "claude_desktop_config.json"
    
    # 确保目录存在
    mcp_config_dir.mkdir(parents=True, exist_ok=True)
    
    # 获取当前脚本的绝对路径
    current_dir = Path(__file__).parent.absolute()
    server_path = current_dir / "main.py"
    
    mcp_config = {
        "mcpServers": {
            "ssh-agent": {
                "command": sys.executable,
                "args": [str(server_path)],
                "env": {
                    "SSH_CONFIG_PATH": str(current_dir / "ssh_config.json")
                }
            }
        }
    }
    
    try:
        with open(mcp_config_file, 'w', encoding='utf-8') as f:
            json.dump(mcp_config, f, indent=2, ensure_ascii=False)
        print(f"✅ MCP客户端配置已创建: {mcp_config_file}")
        print("🔄 请重启Claude Desktop以加载新的MCP服务器")
    except Exception as e:
        print(f"❌ 创建MCP客户端配置失败: {e}")

def verify_installation():
    """验证安装"""
    print("🔍 验证安装...")
    try:
        # 测试导入模块
        from config_loader import ConfigLoader
        from ssh_manager import SSHManager
        from mcp_server import server
        
        # 测试配置加载
        config_loader = ConfigLoader()
        config_loader.load_config()
        
        print("✅ 安装验证成功")
        return True
    except Exception as e:
        print(f"❌ 安装验证失败: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="SSH Agent MCP 服务安装脚本")
    parser.add_argument("--no-deps", action="store_true", help="跳过依赖安装")
    parser.add_argument("--no-config", action="store_true", help="跳过配置文件创建")
    parser.add_argument("--no-mcp-config", action="store_true", help="跳过MCP客户端配置创建")
    
    args = parser.parse_args()
    
    print("🚀 开始安装 SSH Agent MCP 服务")
    print("=" * 50)
    
    # 安装依赖
    if not args.no_deps:
        install_dependencies()
    
    # 创建配置文件
    if not args.no_config:
        create_example_config()
    
    # 创建MCP客户端配置
    if not args.no_mcp_config:
        create_mcp_client_config()
    
    # 验证安装
    if verify_installation():
        print("\n🎉 安装完成！")
        print("\n📋 后续步骤:")
        print("1. 编辑 ssh_config.json 文件，添加您的SSH连接信息")
        print("2. 重启 Claude Desktop 以加载MCP服务器")
        print("3. 在Claude中使用SSH相关工具")
        print("\n💡 使用方法:")
        print("- 使用 ssh_list_config 查看配置的连接")
        print("- 使用 ssh_connect_by_name 通过配置名称连接")
        print("- 使用 ssh_auto_connect 自动连接标记的连接")
    else:
        print("\n❌ 安装失败，请检查错误信息")
        sys.exit(1)

if __name__ == "__main__":
    main()
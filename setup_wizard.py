#!/usr/bin/env python3
"""
SSH Agent MCP 配置向导
帮助用户快速创建和配置SSH连接
"""

import json
import os
import sys
from pathlib import Path
from getpass import getpass
from config_loader import SSHAgentConfig, SSHConnectionConfig

def get_user_input(prompt, required=True, default=None, password=False):
    """获取用户输入"""
    while True:
        if password:
            value = getpass(prompt)
        else:
            if default:
                value = input(f"{prompt} [{default}]: ").strip()
                if not value:
                    value = default
            else:
                value = input(f"{prompt}: ").strip()
        
        if not value and required:
            print("此字段为必填项，请重新输入。")
            continue
        
        return value

def get_yes_no(prompt, default=True):
    """获取是/否输入"""
    default_str = "Y/n" if default else "y/N"
    while True:
        value = input(f"{prompt} [{default_str}]: ").strip().lower()
        if not value:
            return default
        if value in ['y', 'yes', '是']:
            return True
        elif value in ['n', 'no', '否']:
            return False
        print("请输入 y(是) 或 n(否)")

def configure_connection():
    """配置单个SSH连接"""
    print("\n=== 配置SSH连接 ===")
    
    name = get_user_input("连接名称（用于标识）", required=True)
    
    # 检查是否已存在同名连接
    config_path = Path.cwd() / "ssh_config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
            
            for conn in existing_config.get('connections', []):
                if conn.get('name') == name:
                    print(f"⚠️  连接名称 '{name}' 已存在")
                    if not get_yes_no("是否覆盖现有配置？", default=False):
                        return None
        except:
            pass
    
    host = get_user_input("SSH服务器地址", required=True)
    username = get_user_input("SSH用户名", required=True)
    port = int(get_user_input("SSH端口", default="22"))
    
    description = get_user_input("连接描述（可选）", required=False)
    
    # 标签
    tags_input = get_user_input("标签（用逗号分隔，如：production,web）", required=False)
    tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
    
    # 认证方式
    print("\n选择认证方式:")
    print("1. 密码认证")
    print("2. 私钥认证")
    
    while True:
        auth_choice = input("请选择 [1]: ").strip()
        if not auth_choice:
            auth_choice = "1"
        
        if auth_choice == "1":
            password = get_user_input("SSH密码", required=True, password=True)
            private_key = None
            private_key_password = None
            break
        elif auth_choice == "2":
            private_key = get_user_input("私钥文件路径", required=True)
            if os.path.exists(private_key):
                has_key_password = get_yes_no("私钥是否有密码？", default=False)
                if has_key_password:
                    private_key_password = get_user_input("私钥密码", required=True, password=True)
                else:
                    private_key_password = None
            else:
                print(f"⚠️  私钥文件不存在: {private_key}")
                continue
            password = None
            break
        else:
            print("请输入 1 或 2")
    
    return SSHConnectionConfig(
        name=name,
        host=host,
        username=username,
        port=port,
        password=password,
        private_key=private_key,
        private_key_password=private_key_password,
        description=description,
        tags=tags
    )

def configure_global_settings():
    """配置全局设置"""
    print("\n=== 全局设置 ===")
    
    default_timeout = int(get_user_input("默认命令超时时间（秒）", default="30"))
    log_level = get_user_input("日志级别 (DEBUG/INFO/WARNING/ERROR)", default="INFO").upper()
    
    # 自动连接
    auto_connect = []
    if get_yes_no("是否设置自动连接？", default=False):
        config_path = Path.cwd() / "ssh_config.json"
        available_connections = []
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    existing_config = json.load(f)
                available_connections = [conn.get('name') for conn in existing_config.get('connections', [])]
            except:
                pass
        
        if available_connections:
            print("\n可用连接:")
            for i, conn_name in enumerate(available_connections, 1):
                print(f"{i}. {conn_name}")
            
            while True:
                choice = input("选择要自动连接的连接编号（多个用逗号分隔）: ").strip()
                if not choice:
                    break
                
                try:
                    indices = [int(i.strip()) - 1 for i in choice.split(',')]
                    for idx in indices:
                        if 0 <= idx < len(available_connections):
                            auto_connect.append(available_connections[idx])
                    break
                except:
                    print("输入格式错误，请重新输入")
    
    max_connections = int(get_user_input("最大连接数", default="10"))
    
    return {
        "default_timeout": default_timeout,
        "log_level": log_level,
        "auto_connect": auto_connect,
        "max_connections": max_connections
    }

def save_config(connections, global_settings):
    """保存配置"""
    config = SSHAgentConfig(
        connections=connections,
        **global_settings
    )
    
    config_path = Path.cwd() / "ssh_config.json"
    
    try:
        config_dict = config.model_dump()
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 配置已保存到: {config_path}")
        print(f"📊 配置了 {len(connections)} 个SSH连接")
        
        if global_settings['auto_connect']:
            print(f"🚀 自动连接: {', '.join(global_settings['auto_connect'])}")
        
        return True
    except Exception as e:
        print(f"\n❌ 保存配置失败: {e}")
        return False

def main():
    """主函数"""
    print("🧙 SSH Agent MCP 配置向导")
    print("=" * 50)
    print("这个向导将帮助您创建SSH连接配置文件")
    
    # 检查现有配置
    config_path = Path.cwd() / "ssh_config.json"
    existing_connections = []
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
            existing_connections = existing_config.get('connections', [])
            print(f"\n📋 发现现有配置文件，包含 {len(existing_connections)} 个连接")
            
            if get_yes_no("是否要查看现有连接？", default=False):
                for conn in existing_connections:
                    print(f"  - {conn.get('name', '未命名')} ({conn.get('username')}@{conn.get('host')}:{conn.get('port', 22)})")
        except Exception as e:
            print(f"⚠️  读取现有配置文件失败: {e}")
    
    # 配置连接
    connections = []
    
    if get_yes_no("是否添加新的SSH连接？", default=not existing_connections):
        while True:
            conn = configure_connection()
            if conn:
                connections.append(conn)
                print(f"✅ 已添加连接: {conn.name}")
            
            if not get_yes_no("是否继续添加连接？", default=False):
                break
    
    # 如果没有新连接，保留现有连接
    if not connections and existing_connections:
        connections = [SSHConnectionConfig(**conn) for conn in existing_connections]
    
    # 配置全局设置
    print("\n" + "=" * 50)
    global_settings = configure_global_settings()
    
    # 保存配置
    print("\n" + "=" * 50)
    if save_config(connections, global_settings):
        print("\n🎉 配置完成！")
        print("\n📋 下一步:")
        print("1. 启动MCP服务: python main.py")
        print("2. 在Claude中使用: ssh_list_config 查看配置")
        print("3. 使用: ssh_connect_by_name 连接到服务器")
        
        if get_yes_no("\n是否现在测试配置？", default=False):
            print("\n🧪 测试配置...")
            try:
                from config_loader import ConfigLoader
                loader = ConfigLoader()
                config = loader.load_config()
                print("✅ 配置文件格式正确")
                print(f"📊 加载了 {len(config.connections)} 个连接配置")
            except Exception as e:
                print(f"❌ 配置测试失败: {e}")
    else:
        print("\n❌ 配置保存失败")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 配置已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 配置向导出错: {e}")
        sys.exit(1)

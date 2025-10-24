#!/usr/bin/env python3
"""
SSH Agent MCP 服务打包脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import zipfile
import tarfile

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    dirs_to_clean = ["build", "dist", "*.egg-info"]
    for pattern in dirs_to_clean:
        for path in Path.cwd().glob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
                print(f"  删除目录: {path}")
            elif path.is_file():
                path.unlink()
                print(f"  删除文件: {path}")

def build_wheel():
    """构建wheel包"""
    print("🔨 构建wheel包...")
    try:
        subprocess.check_call([sys.executable, "-m", "build", "--wheel"])
        print("✅ Wheel包构建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Wheel包构建失败: {e}")
        return False

def build_sdist():
    """构建源码包"""
    print("🔨 构建源码包...")
    try:
        subprocess.check_call([sys.executable, "-m", "build", "--sdist"])
        print("✅ 源码包构建成功")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 源码包构建失败: {e}")
        return False

def create_portable_package():
    """创建便携式包"""
    print("📦 创建便携式包...")
    
    # 创建临时目录
    portable_dir = Path.cwd() / "dist" / "ssh-agent-mcp-portable"
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    portable_dir.mkdir(parents=True)
    
    # 复制必要文件
    files_to_copy = [
        "main.py",
        "mcp_server.py", 
        "ssh_manager.py",
        "config_loader.py",
        "pyproject.toml",
        "README.md",
        "install.py"
    ]
    
    for file_name in files_to_copy:
        src = Path.cwd() / file_name
        dst = portable_dir / file_name
        if src.exists():
            shutil.copy2(src, dst)
            print(f"  复制: {file_name}")
        else:
            print(f"  ⚠️  文件不存在: {file_name}")
    
    # 创建requirements.txt
    requirements = """mcp>=1.0.0
paramiko>=3.0.0
pydantic>=2.0.0
"""
    with open(portable_dir / "requirements.txt", "w") as f:
        f.write(requirements)
    print("  创建: requirements.txt")
    
    # 创建启动脚本
    start_script = """#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main
if __name__ == "__main__":
    main()
"""
    with open(portable_dir / "start_ssh_agent.py", "w") as f:
        f.write(start_script)
    os.chmod(portable_dir / "start_ssh_agent.py", 0o755)
    print("  创建: start_ssh_agent.py")
    
    # 创建示例配置
    example_config = """{
  "connections": [
    {
      "name": "example-server",
      "host": "192.168.1.100",
      "username": "admin",
      "port": 22,
      "password": "your_password",
      "description": "示例服务器配置",
      "tags": ["example", "test"]
    }
  ],
  "default_timeout": 30,
  "log_level": "INFO",
  "auto_connect": [],
  "max_connections": 10
}"""
    with open(portable_dir / "ssh_config.example.json", "w") as f:
        f.write(example_config)
    print("  创建: ssh_config.example.json")
    
    # 创建便携式说明
    portable_readme = """# SSH Agent MCP 便携式版本

## 快速开始

1. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

2. 复制配置文件:
   ```bash
   cp ssh_config.example.json ssh_config.json
   ```

3. 编辑配置文件，添加您的SSH连接信息

4. 启动服务:
   ```bash
   python start_ssh_agent.py
   ```

## 配置MCP客户端

在Claude Desktop配置文件中添加:
```json
{
  "mcpServers": {
    "ssh-agent": {
      "command": "python",
      "args": ["/path/to/ssh-agent-mcp-portable/start_ssh_agent.py"],
      "env": {
        "SSH_CONFIG_PATH": "/path/to/ssh-agent-mcp-portable/ssh_config.json"
      }
    }
  }
}
```

## 文件说明

- `start_ssh_agent.py`: 启动脚本
- `ssh_config.json`: SSH连接配置文件
- `requirements.txt`: Python依赖
- `main.py`: 主程序入口
- `mcp_server.py`: MCP服务器实现
- `ssh_manager.py`: SSH连接管理
- `config_loader.py`: 配置文件加载器
"""
    with open(portable_dir / "README_PORTABLE.md", "w") as f:
        f.write(portable_readme)
    print("  创建: README_PORTABLE.md")
    
    # 创建zip包
    zip_path = Path.cwd() / "dist" / "ssh-agent-mcp-portable.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in portable_dir.rglob('*'):
            if file_path.is_file():
                arcname = file_path.relative_to(portable_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ 便携式包已创建: {zip_path}")
    
    # 创建tar.gz包
    tar_path = Path.cwd() / "dist" / "ssh-agent-mcp-portable.tar.gz"
    with tarfile.open(tar_path, 'w:gz') as tarf:
        tarf.add(portable_dir, arcname="ssh-agent-mcp-portable")
    
    print(f"✅ 便携式包已创建: {tar_path}")
    
    # 清理临时目录
    shutil.rmtree(portable_dir)
    
    return True

def main():
    import argparse
    parser = argparse.ArgumentParser(description="SSH Agent MCP 服务打包脚本")
    parser.add_argument("--clean", action="store_true", help="仅清理构建目录")
    parser.add_argument("--wheel", action="store_true", help="仅构建wheel包")
    parser.add_argument("--sdist", action="store_true", help="仅构建源码包")
    parser.add_argument("--portable", action="store_true", help="仅创建便携式包")
    parser.add_argument("--all", action="store_true", help="构建所有包格式")
    
    args = parser.parse_args()
    
    print("🚀 开始打包 SSH Agent MCP 服务")
    print("=" * 50)
    
    # 清理
    clean_build()
    
    if args.clean:
        print("✅ 清理完成")
        return
    
    success = True
    
    # 构建wheel包
    if args.all or args.wheel or not any([args.wheel, args.sdist, args.portable]):
        if not build_wheel():
            success = False
    
    # 构建源码包
    if args.all or args.sdist:
        if not build_sdist():
            success = False
    
    # 创建便携式包
    if args.all or args.portable:
        if not create_portable_package():
            success = False
    
    if success:
        print("\n🎉 打包完成！")
        print("\n📦 生成的包:")
        dist_dir = Path.cwd() / "dist"
        if dist_dir.exists():
            for file_path in dist_dir.iterdir():
                if file_path.is_file():
                    size = file_path.stat().st_size / 1024 / 1024  # MB
                    print(f"  {file_path.name} ({size:.1f} MB)")
    else:
        print("\n❌ 打包失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
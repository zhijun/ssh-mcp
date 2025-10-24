# SSH Agent MCP 部署和使用指南

本文档详细介绍如何将SSH Agent MCP服务发布到PyPI，以及Claude Desktop用户如何使用这个MCP服务。

## 📦 发布到PyPI

### 1. 准备工作

#### 1.1 安装发布工具
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装构建和发布工具
pip install build twine
```

#### 1.2 注册PyPI账户
1. 访问 [PyPI官网](https://pypi.org) 注册账户
2. 验证邮箱地址
3. 启用双因素认证（2FA）- 现在PyPI强制要求
4. 生成API Token：
   - 登录PyPI → Account Settings → API tokens
   - 创建新token，选择权限范围（建议选择"Entire account"）
   - 复制生成的token（只显示一次）

### 2. 构建分发包

#### 2.1 检查项目结构
确保项目包含以下文件：
```
sshagent/
├── main.py              # 主入口文件
├── mcp_server.py        # MCP服务器实现
├── ssh_manager.py       # SSH连接管理器
├── config_loader.py     # 配置文件加载器
├── setup.py             # 构建脚本
├── pyproject.toml       # 项目配置
└── README.md            # 说明文档
```

#### 2.2 构建包
```bash
# 构建wheel和源码包
python setup.py sdist bdist_wheel

# 检查生成的包
ls dist/
# 应该看到类似：
# ssh_agent_mcp-0.1.0-py3-none-any.whl
# ssh_agent_mcp-0.1.0.tar.gz
```

#### 2.3 验证包完整性
```bash
# 检查包是否符合PyPI标准
python -m twine check dist/*
# 应该显示：PASSED
```

### 3. 发布流程

#### 3.1 测试发布（推荐）
```bash
# 发布到测试PyPI
python -m twine upload --repository testpypi dist/*

# 安装测试版本验证
pip install --index-url https://test.pypi.org/simple/ ssh-agent-mcp
```

#### 3.2 正式发布
```bash
# 发布到正式PyPI（交互式）
# 当命令提示输入用户名/密码时：
# 用户名填 "__token__"，密码填你在PyPI复制的 API Token（形如 pypi-xxxxxxxx...）
python -m twine upload dist/*

# 或者在命令中直接使用token（推荐，避免交互）
python -m twine upload dist/* --username __token__ --password pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

提示：
- 如果使用第一种交互方式，输入 `__token__` 作为用户名，粘贴你之前复制的 API Token 作为密码即可完成认证。
- 为了避免在命令历史中暴露 token，也可以使用环境变量：
```bash
export TWINE_USERNAME="__token__"
export TWINE_PASSWORD="pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
python -m twine upload dist/*
```
- 或者在 `~/.pypirc` 中配置：
```ini
[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- TestPyPI 配置示例：
```ini
[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- 使用 TestPyPI 配置进行上传与安装：
```bash
python -m twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ ssh-agent-mcp
```

### 4. 验证发布

#### 4.1 检查PyPI页面
- 访问 https://pypi.org/project/ssh-agent-mcp/
- 确认包信息正确显示

#### 4.2 测试安装
```bash
# 清理本地缓存
pip cache purge

# 安装发布的包
pip install ssh-agent-mcp

# 验证命令行工具
ssh-agent-mcp --help
```

### 5. 版本管理

#### 5.1 更新版本号
编辑 `pyproject.toml`：
```toml
[project]
name = "ssh-agent-mcp"
version = "0.1.1"  # 更新版本号
```

#### 5.2 重新发布
```bash
# 清理旧的构建文件
rm -rf build/ dist/ *.egg-info/

# 重新构建和发布
python setup.py sdist bdist_wheel
python -m twine upload dist/*
```

## 👤 Claude Desktop 用户使用指南

### 1. 基本配置

#### 1.1 找到Claude Desktop配置文件
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude-desktop/claude_desktop_config.json`

#### 1.2 最简单的配置
```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": ["ssh-agent-mcp@latest"]
    }
  }
}
```

### 2. 使用方式

#### 2.1 方式一：无参数启动（推荐）
MCP服务启动后等待大模型提供连接参数：

```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": ["ssh-agent-mcp@latest"]
    }
  }
}
```

**使用流程**：
1. 重启Claude Desktop
2. 对大模型说："请连接到SSH服务器 192.168.1.100，用户名是admin"
3. 大模型会自动调用ssh_connect工具建立连接

#### 2.2 方式二：命令行参数配置
直接在配置中提供连接参数：

```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--host=192.168.1.100",
        "--user=admin",
        "--password=your_password",
        "--auto-connect"
      ]
    }
  }
}
```

#### 2.3 方式三：使用私钥认证

```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--host=prod.example.com",
        "--user=admin",
        "--key=/home/user/.ssh/id_rsa",
        "--auto-connect"
      ]
    }
  }
}
```

### 3. 高级配置

#### 3.1 使用配置文件
创建SSH配置文件 `ssh_config.json`：
```json
{
  "connections": [
    {
      "name": "production-server",
      "host": "prod.example.com",
      "username": "admin",
      "private_key": "/home/user/.ssh/id_rsa",
      "description": "生产环境服务器",
      "tags": ["production", "critical"]
    },
    {
      "name": "development-server",
      "host": "192.168.1.100",
      "username": "dev",
      "password": "dev_password",
      "description": "开发环境服务器",
      "tags": ["development", "test"]
    }
  ],
  "auto_connect": ["production-server"]
}
```

Claude Desktop配置：
```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--config=/path/to/ssh_config.json",
        "--connection=production-server"
      ]
    }
  }
}
```

#### 3.2 多服务器配置
```json
{
  "mcpServers": {
    "ssh-prod": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--config=/path/to/prod_config.json",
        "--connection=prod-server",
        "--auto-connect"
      ]
    },
    "ssh-dev": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--config=/path/to/dev_config.json",
        "--connection=dev-server"
      ]
    }
  }
}
```

### 4. 使用示例

#### 4.1 基本操作
```
用户：请连接到我的服务器 192.168.1.100，用户名是admin，密码是password123

Claude：我来帮您连接到SSH服务器。
[自动调用ssh_connect工具]

SSH连接建立成功
连接ID: admin@192.168.1.100:22
主机: admin@192.168.1.100:22

用户：请查看服务器上的/home目录内容

Claude：我来为您查看/home目录的内容。
[自动调用ssh_execute工具]

命令执行结果:
连接ID: admin@192.168.1.100:22
命令: ls -la /home
成功: true
退出码: 0
标准输出:
total 12
drwxr-xr-x  3 root root 4096 Oct 23 10:30 .
drwxr-xr-x  3 root root 4096 Oct 23 10:00 ..
drwxr-xr-x  2 admin admin 4096 Oct 23 10:30 admin
```

#### 4.2 异步命令
```
用户：请监控服务器日志，显示最新的错误信息

Claude：我来启动日志监控命令。
[自动调用ssh_start_async_command工具]

异步命令已启动
命令ID: cmd-uuid-1234
连接ID: admin@192.168.1.100:22
命令: tail -f /var/log/nginx/error.log

使用 ssh_get_command_status 工具查询命令状态和输出

用户：请显示最新的日志输出

Claude：我来获取最新的日志输出。
[自动调用ssh_get_command_status工具]

异步命令状态:
命令ID: cmd-uuid-1234
连接ID: admin@192.168.1.100:22
命令: tail -f /var/log/nginx/error.log
状态: running
标准输出:
2023/10/23 10:35:12 [error] 1234#0: *1 connect() failed (111: Connection refused)
```

### 5. 故障排除

#### 5.1 常见问题

**问题1：MCP服务无法启动**
```bash
# 检查Python版本
python --version  # 需要3.12+

# 手动测试
uvx ssh-agent-mcp@latest --help
```

**问题2：SSH连接失败**
- 检查服务器地址和端口
- 验证用户名和密码/私钥
- 确认SSH服务正在运行
- 检查防火墙设置

**问题3：私钥认证失败**
- 确认私钥文件路径正确
- 检查私钥权限（应为600）
- 如果私钥有密码，提供private_key_password

#### 5.2 调试模式

启用详细日志：
```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--log-level=DEBUG"
      ]
    }
  }
}
```

### 6. 最佳实践

#### 6.1 安全建议
- 使用私钥认证而非密码认证
- 定期轮换SSH密钥
- 不要在配置文件中明文存储密码
- 使用SSH代理转发

#### 6.2 性能优化
- 合理设置超时时间
- 定期清理已完成的异步命令
- 使用连接池避免频繁连接

#### 6.3 连接管理
- 使用有意义的连接名称
- 为连接添加标签便于管理
- 定期检查连接状态
- 及时断开不需要的连接

## 🚀 快速开始

### 对于开发者
```bash
# 1. 克隆项目
git clone https://github.com/yourusername/sshagent.git
cd sshagent

# 2. 构建和发布
python setup.py sdist bdist_wheel
python -m twine upload dist/*
```

### 对于用户
```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": ["ssh-agent-mcp@latest"]
    }
  }
}
```

重启Claude Desktop，然后就可以说："请连接到我的SSH服务器"开始使用了！

---

## 📞 支持

- **项目地址**: https://github.com/yourusername/sshagent
- **问题反馈**: https://github.com/yourusername/sshagent/issues
- **PyPI页面**: https://pypi.org/project/ssh-agent-mcp/
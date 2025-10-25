# SSH Agent MCP 服务

这是一个基于Python的MCP (Model Context Protocol) stdio服务，允许大模型直接操作SSH连接来解决远程服务器问题。支持通过命令行参数或JSON配置文件管理SSH连接，让用户通过简单的JSON配置即可使用。

## 功能特性

- **⚡ uvx支持**: 通过 `uvx ssh-agent-mcp` 一键运行，无需本地安装
- **🔧 命令行参数**: 支持完整的命令行参数配置，无需配置文件
- **🔧 JSON配置管理**: 通过简单的JSON文件管理多个SSH连接
- **🔗 有状态连接管理**: 维护SSH连接状态，支持多个并发连接
- **🔐 多种认证方式**: 支持密码认证、私钥认证和SSH Agent
- **⚡ 命令执行**: 在远程服务器上执行命令并获取输出
- **🔄 异步命令支持**: 支持长时间运行的命令（如top、tail等），实时获取输出
- **🎮 交互式命令支持**: 支持需要用户输入的交互式命令（如sudo、vim、mysql、python等）
- **📊 命令生命周期管理**: 启动、监控、终止和清理异步命令和交互式会话
- **📈 连接状态查询**: 实时查询连接状态和管理连接
- **🚀 自动连接**: 支持启动时自动连接指定的服务器
- **📁 SFTP文件传输**: 支持文件上传、下载和目录操作
- **📂 远程文件管理**: 支持远程目录浏览、创建、删除和重命名

## 🚀 快速开始

### 方法一：uvx 一键运行（推荐）

在Claude Desktop的配置文件中添加：

```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--host=192.168.1.100",
        "--user=root",
        "--password=your_password",
        "--timeout=30000"
      ]
    }
  }
}
```

重启Claude Desktop即可使用！

**⭐ 新特性：无参数启动**

MCP服务可以不传入任何SSH连接参数启动，等待大模型通过工具提供连接信息：

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

启动后，大模型可以使用 `ssh_connect` 或 `ssh_connect_by_name` 工具建立连接。

### 方法二：本地安装

```bash
# 安装
pip install ssh-agent-mcp

# 或从源码安装
git clone https://github.com/yourusername/sshagent.git
cd sshagent
pip install -e .
```

### 方法三：使用配置文件

1. 创建配置文件 `ssh_config.json`:
```json
{
  "connections": [
    {
      "name": "production-server",
      "host": "prod.example.com",
      "username": "admin",
      "private_key": "/home/user/.ssh/id_rsa",
      "tags": ["production"]
    }
  ],
  "auto_connect": ["production-server"]
}
```

2. 在Claude Desktop中配置:
```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--config=/path/to/ssh_config.json",
        "--connection=production-server",
        "--auto-connect"
      ]
    }
  }
}
```

## 📝 使用方式

### 方式一：无参数启动（推荐）⭐

最灵活的方式，启动时不传入任何连接参数，由大模型动态管理连接：

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

**优势**：
- 🔄 **动态连接管理**：大模型可以根据需要连接不同的服务器
- 🛡️ **安全性更高**：不在配置文件中暴露敏感信息
- 🎯 **灵活性强**：支持多服务器切换，适合复杂场景

### 方式二：纯命令行参数

直接在Claude Desktop配置中指定所有参数：

```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--host=192.168.1.100",
        "--port=22",
        "--user=root",
        "--password=your_password",
        "--timeout=30000",
        "--max-chars=none"
      ]
    }
  }
}
```

### 方式三：命令行 + 配置文件

结合配置文件和命令行参数：

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

### 方式三：使用私钥认证

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
        "--key-password=private_key_password"
      ]
    }
  }
}
```

### 方式四：配置文件模式

使用配置文件管理多个连接：

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

## 🔧 命令行参数

| 参数 | 描述 | 必需 | 示例 |
|------|------|------|------|
| `--host` | SSH服务器地址 | 否* | `192.168.1.100` |
| `--user`, `--username` | SSH用户名 | 否* | `root` |
| `--port` | SSH端口 | 否 | `22` (默认) |
| `--password` | SSH密码 | 否 | `your_password` |
| `--key`, `--private-key` | 私钥文件路径 | 否 | `/home/user/.ssh/id_rsa` |
| `--key-password`, `--private-key-password` | 私钥密码 | 否 | `key_password` |
| `--config`, `-c` | 配置文件路径 | 否 | `/path/to/config.json` |
| `--connection` | 配置文件中的连接名称 | 否 | `production-server` |
| `--timeout` | 命令超时时间（毫秒） | 否 | `30000` (默认) |
| `--max-chars` | 最大输出字符数 | 否 | `none` (默认) |
| `--log-level` | 日志级别 | 否 | `INFO` (默认) |
| `--auto-connect` | 启动时自动连接 | 否 | - |

**注意**：
- `*` 标记的参数在使用配置文件或无参数启动模式时不是必需的
- 无参数启动时，所有连接参数都是可选的，MCP服务将等待大模型通过工具提供连接信息

## 📋 配置文件格式

当使用配置文件时，`ssh_config.json` 格式如下：

```json
{
  "connections": [
    {
      "name": "production-server",
      "host": "prod.example.com",
      "username": "admin",
      "port": 22,
      "private_key": "/home/user/.ssh/id_rsa",
      "description": "生产环境服务器",
      "tags": ["production", "critical"]
    },
    {
      "name": "dev-server",
      "host": "192.168.1.100",
      "username": "dev",
      "port": 22,
      "password": "dev_password",
      "description": "开发环境服务器",
      "tags": ["development", "test"]
    }
  ],
  "default_timeout": 30,
  "log_level": "INFO",
  "auto_connect": ["production-server"],
  "max_connections": 10
}
```

## 🛠️ MCP工具接口

该服务提供以下MCP工具：

### 基础连接工具

#### 1. ssh_connect_by_name ⭐ 推荐
使用配置文件中的连接名称建立SSH连接
- **参数**:
  - `connection_name` (必需): 配置文件中的连接名称
- **示例**:
```json
{
  "name": "ssh_connect_by_name",
  "arguments": {
    "connection_name": "production-server"
  }
}
```

#### 2. ssh_connect
手动建立SSH连接（不推荐，建议使用配置文件）
- **参数**:
  - `host` (必需): SSH服务器主机名或IP地址
  - `username` (必需): SSH用户名
  - `port` (可选): SSH端口，默认为22
  - `password` (可选): SSH密码
  - `private_key` (可选): 私钥文件路径
  - `private_key_password` (可选): 私钥密码

#### 3. ssh_disconnect
断开SSH连接
- **参数**:
  - `connection_id` (必需): SSH连接ID

#### 4. ssh_disconnect_all
断开所有SSH连接
- **参数**: 无

### 配置管理工具

#### 5. ssh_list_config ⭐ 新功能
列出配置文件中的所有SSH连接
- **参数**:
  - `filter_tag` (可选): 按标签过滤连接
- **示例**:
```json
{
  "name": "ssh_list_config",
  "arguments": {
    "filter_tag": "production"
  }
}
```

#### 6. ssh_auto_connect ⭐ 新功能
自动连接配置文件中标记为auto_connect的连接
- **参数**: 无

### 状态查询工具

#### 7. ssh_status
查询SSH连接状态
- **参数**:
  - `connection_id` (可选): SSH连接ID，不提供则返回所有连接状态

#### 8. ssh_list_connections
列出所有SSH连接
- **参数**: 无

### 命令执行工具

#### 9. ssh_execute
在SSH连接上执行命令
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `command` (必需): 要执行的命令
  - `timeout` (可选): 命令超时时间（秒），默认为30

### 异步命令工具

#### 10. ssh_start_async_command
启动长时间运行的异步命令
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `command` (必需): 要执行的长时间运行命令

#### 11. ssh_get_command_status
获取异步命令状态和最新输出
- **参数**:
  - `command_id` (必需): 异步命令ID

#### 12. ssh_list_async_commands
列出所有异步命令状态
- **参数**: 无

#### 13. ssh_terminate_command
终止正在运行的异步命令
- **参数**:
  - `command_id` (必需): 要终止的异步命令ID

#### 14. ssh_cleanup_commands
清理已完成的异步命令
- **参数**:
  - `max_age` (可选): 保留时间（秒），默认3600秒

### 交互式命令工具 🎮 新功能

#### 15. ssh_start_interactive
启动交互式命令会话，支持需要用户输入的命令
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `command` (必需): 要执行的交互式命令
  - `pty_width` (可选): 伪终端宽度，默认80
  - `pty_height` (可选): 伪终端高度，默认24
- **示例**:
```json
{
  "name": "ssh_start_interactive",
  "arguments": {
    "connection_id": "user@server:22",
    "command": "sudo -i",
    "pty_width": 120,
    "pty_height": 30
  }
}
```

#### 16. ssh_send_input
向交互式会话发送输入
- **参数**:
  - `session_id` (必需): 交互式会话ID
  - `input_text` (必需): 要发送的输入内容
- **示例**:
```json
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session-uuid",
    "input_text": "password123\n"
  }
}
```

#### 17. ssh_get_interactive_output
获取交互式会话的输出
- **参数**:
  - `session_id` (必需): 交互式会话ID
  - `max_lines` (可选): 最大输出行数，默认100
- **示例**:
```json
{
  "name": "ssh_get_interactive_output",
  "arguments": {
    "session_id": "session-uuid",
    "max_lines": 50
  }
}
```

#### 18. ssh_list_interactive_sessions
列出指定连接的所有交互式会话
- **参数**:
  - `connection_id` (可选): SSH连接ID，不提供则返回所有连接的会话
- **示例**:
```json
{
  "name": "ssh_list_interactive_sessions",
  "arguments": {
    "connection_id": "user@server:22"
  }
}
```

#### 19. ssh_terminate_interactive
终止交互式会话
- **参数**:
  - `session_id` (必需): 交互式会话ID
- **示例**:
```json
{
  "name": "ssh_terminate_interactive",
  "arguments": {
    "session_id": "session-uuid"
  }
}
```

#### 20. ssh_connect_by_config_host ⭐ 新功能
使用SSH config文件中的主机名建立连接
- **参数**:
  - `config_host` (必需): SSH config文件中的主机名
  - `username` (可选): 可选用户名，覆盖config中的设置
  - `password` (可选): 可选密码
  - `private_key` (可选): 可选私钥文件路径
  - `private_key_password` (可选): 可选私钥密码
- **示例**:
```json
{
  "name": "ssh_connect_by_config_host",
  "arguments": {
    "config_host": "my-server"
  }
}
```

**优势**：
- 🎯 **简化配置**：直接使用~/.ssh/config中已配置的主机
- 🔗 **自动解析**：SSH客户端自动处理主机名、端口、用户等配置
- 🛡️ **安全性**：利用SSH config的现有安全配置
- 📦 **零配置**：无需额外配置文件，直接使用标准SSH配置

## 📁 SFTP文件传输工具 ⭐ 新功能

#### 21. ssh_upload_file
上传文件到远程服务器
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `local_path` (必需): 本地文件路径
  - `remote_path` (必需): 远程文件路径
- **示例**:
```json
{
  "name": "ssh_upload_file",
  "arguments": {
    "connection_id": "connection-uuid",
    "local_path": "/path/to/local/file.txt",
    "remote_path": "/remote/path/file.txt"
  }
}
```

#### 22. ssh_download_file
从远程服务器下载文件
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `remote_path` (必需): 远程文件路径
  - `local_path` (必需): 本地文件路径
- **示例**:
```json
{
  "name": "ssh_download_file",
  "arguments": {
    "connection_id": "connection-uuid",
    "remote_path": "/remote/path/file.txt",
    "local_path": "/path/to/local/downloaded_file.txt"
  }
}
```

#### 23. ssh_list_remote_directory
列出远程目录内容
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `remote_path` (可选): 远程目录路径，默认为当前目录
- **示例**:
```json
{
  "name": "ssh_list_remote_directory",
  "arguments": {
    "connection_id": "connection-uuid",
    "remote_path": "/home/user/documents"
  }
}
```

#### 24. ssh_create_remote_directory
在远程服务器上创建目录
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `remote_path` (必需): 要创建的远程目录路径
  - `mode` (可选): 目录权限，默认为755
  - `parents` (可选): 是否递归创建父目录，默认为true
- **示例**:
```json
{
  "name": "ssh_create_remote_directory",
  "arguments": {
    "connection_id": "connection-uuid",
    "remote_path": "/remote/new/directory",
    "mode": 755,
    "parents": true
  }
}
```

#### 25. ssh_remove_remote_file
删除远程文件或目录
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `remote_path` (必需): 要删除的远程文件或目录路径
- **示例**:
```json
{
  "name": "ssh_remove_remote_file",
  "arguments": {
    "connection_id": "connection-uuid",
    "remote_path": "/remote/path/to/delete"
  }
}
```

#### 26. ssh_get_remote_file_info
获取远程文件或目录信息
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `remote_path` (必需): 远程文件或目录路径
- **示例**:
```json
{
  "name": "ssh_get_remote_file_info",
  "arguments": {
    "connection_id": "connection-uuid",
    "remote_path": "/remote/path/file.txt"
  }
}
```

#### 27. ssh_rename_remote_path
重命名远程文件或目录
- **参数**:
  - `connection_id` (必需): SSH连接ID
  - `old_path` (必需): 原始路径
  - `new_path` (必需): 新路径
- **示例**:
```json
{
  "name": "ssh_rename_remote_path",
  "arguments": {
    "connection_id": "connection-uuid",
    "old_path": "/remote/old_name.txt",
    "new_path": "/remote/new_name.txt"
  }
}
```

## 📖 使用示例

### 启动MCP服务
```bash
python main.py
```

### 🌟 无参数启动工作流程（推荐）

**适用场景**：动态连接管理，多服务器操作，安全性要求高的环境

1. **手动建立连接**:
```json
{
  "name": "ssh_connect",
  "arguments": {
    "host": "192.168.1.100",
    "username": "admin",
    "password": "secure_password"
  }
}
```

2. **查看连接状态**:
```json
{
  "name": "ssh_list_connections",
  "arguments": {}
}
```

3. **执行命令**:
```json
{
  "name": "ssh_execute",
  "arguments": {
    "connection_id": "admin@192.168.1.100:22",
    "command": "systemctl status nginx"
  }
}
```

4. **连接其他服务器**:
```json
{
  "name": "ssh_connect",
  "arguments": {
    "host": "prod.example.com",
    "username": "root",
    "private_key": "/home/user/.ssh/id_rsa"
  }
}
```

### 🎯 配置文件工作流程

**适用场景**：固定服务器环境，批量操作，团队协作

1. **查看配置的连接**:
```json
{
  "name": "ssh_list_config",
  "arguments": {}
}
```

2. **通过名称建立连接**:
```json
{
  "name": "ssh_connect_by_name",
  "arguments": {
    "connection_name": "production-server"
  }
}
```

3. **执行命令**:
```json
{
  "name": "ssh_execute",
  "arguments": {
    "connection_id": "admin@prod.example.com:22",
    "command": "df -h"
  }
}
```

4. **断开连接**:
```json
{
  "name": "ssh_disconnect",
  "arguments": {
    "connection_id": "admin@prod.example.com:22"
  }
}
```

### 🏠 SSH Config工作流程 ⭐ 新功能

**适用场景**：已有SSH config配置，利用标准SSH配置文件

假设你的 `~/.ssh/config` 文件中有以下配置：

```bash
Host my-server
    HostName 192.168.1.100
    User admin
    Port 22
    IdentityFile ~/.ssh/id_rsa

Host production
    HostName prod.example.com
    User root
    Port 2222
    IdentityFile ~/.ssh/prod_key
```

1. **使用SSH config主机名建立连接**:
```json
{
  "name": "ssh_connect_by_config_host",
  "arguments": {
    "config_host": "my-server"
  }
}
```

2. **覆盖config中的用户名**:
```json
{
  "name": "ssh_connect_by_config_host",
  "arguments": {
    "config_host": "production",
    "username": "deploy"
  }
}
```

3. **使用密码覆盖config中的私钥认证**:
```json
{
  "name": "ssh_connect_by_config_host",
  "arguments": {
    "config_host": "my-server",
    "password": "temporary_password"
  }
}
```

4. **查看连接状态**:
```json
{
  "name": "ssh_status",
  "arguments": {}
}
```

5. **执行命令**:
```json
{
  "name": "ssh_execute",
  "arguments": {
    "connection_id": "my-server",
    "command": "hostname"
  }
}
```

**优势**：
- 🎯 **零配置**：直接使用已有的SSH config配置
- 🔗 **自动解析**：自动处理主机名、端口、用户名、私钥等
- 🛡️ **安全性**：利用SSH config的现有安全设置
- 📦 **标准化**：遵循SSH标准配置约定

### 🚀 自动连接工作流程

1. **启动时自动连接所有标记的服务器**:
```json
{
  "name": "ssh_auto_connect",
  "arguments": {}
}
```

2. **查看所有连接状态**:
```json
{
  "name": "ssh_status",
  "arguments": {}
}
```

### 🔄 异步命令工作流程

1. **启动长时间运行命令**:
```json
{
  "name": "ssh_start_async_command",
  "arguments": {
    "connection_id": "admin@prod.example.com:22",
    "command": "tail -f /var/log/nginx/access.log"
  }
}
```

2. **查询命令状态和输出**:
```json
{
  "name": "ssh_get_command_status",
  "arguments": {
    "command_id": "返回的命令UUID"
  }
}
```

3. **终止长时间运行命令**:
```json
{
  "name": "ssh_terminate_command",
  "arguments": {
    "command_id": "要终止的命令UUID"
  }
}
```

### 🎮 交互式命令工作流程

交互式命令支持让大模型能够与需要用户输入的命令进行实时交互，如 `sudo`、`vim`、`mysql`、`python` 等。

#### 基本交互式会话

1. **启动交互式会话**:
```json
{
  "name": "ssh_start_interactive",
  "arguments": {
    "connection_id": "admin@prod.example.com:22",
    "command": "bash",
    "pty_width": 80,
    "pty_height": 24
  }
}
```

2. **发送命令到会话**:
```json
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "返回的会话UUID",
    "input_text": "ls -la\n"
  }
}
```

3. **获取会话输出**:
```json
{
  "name": "ssh_get_interactive_output",
  "arguments": {
    "session_id": "会话UUID",
    "max_lines": 50
  }
}
```

4. **终止交互式会话**:
```json
{
  "name": "ssh_terminate_interactive",
  "arguments": {
    "session_id": "会话UUID"
  }
}
```

#### 高级交互式场景

**1. sudo 命令交互**:
```json
// 启动交互式会话
{
  "name": "ssh_start_interactive",
  "arguments": {
    "connection_id": "user@server:22",
    "command": "sudo -i"
  }
}

// 发送密码
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session_uuid",
    "input_text": "your_password\n"
  }
}

// 执行管理员命令
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session_uuid",
    "input_text": "systemctl status nginx\n"
  }
}
```

**2. Python 交互式环境**:
```json
// 启动Python解释器
{
  "name": "ssh_start_interactive",
  "arguments": {
    "connection_id": "dev@server:22",
    "command": "python3"
  }
}

// 执行Python代码
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session_uuid",
    "input_text": "import os\nprint(os.getcwd())\n"
  }
}
```

**3. 文本编辑器 (vim/nano)**:
```json
// 启动vim编辑器
{
  "name": "ssh_start_interactive",
  "arguments": {
    "connection_id": "user@server:22",
    "command": "vim /etc/hosts",
    "pty_width": 120,
    "pty_height": 30
  }
}

// 进入插入模式
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session_uuid",
    "input_text": "i"
  }
}

// 输入内容
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session_uuid",
    "input_text": "127.0.0.1 localhost\n"
  }
}

// 保存并退出
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session_uuid",
    "input_text": "\u001b:wq\n"
  }
}
```

**4. 数据库交互 (MySQL)**:
```json
// 连接MySQL
{
  "name": "ssh_start_interactive",
  "arguments": {
    "connection_id": "db@server:22",
    "command": "mysql -u root -p"
  }
}

// 输入密码
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session_uuid",
    "input_text": "database_password\n"
  }
}

// 执行SQL查询
{
  "name": "ssh_send_input",
  "arguments": {
    "session_id": "session_uuid",
    "input_text": "SHOW DATABASES;\n"
  }
}
```

#### 交互式会话管理

**查看所有活跃会话**:
```json
{
  "name": "ssh_list_interactive_sessions",
  "arguments": {
    "connection_id": "user@server:22"
  }
}
```

#### 交互式命令最佳实践

1. **PTY 尺寸设置**:
   - 对于文本编辑器，建议使用较大的终端尺寸 (120x30)
   - 对于简单命令交互，默认尺寸 (80x24) 即可

2. **输入格式**:
   - 命令结尾添加 `\n` 表示回车
   - 特殊键使用转义序列，如 ESC 键: `\u001b`
   - Ctrl+C: `\u0003`, Ctrl+D: `\u0004`

3. **输出缓冲**:
   - 定期获取输出避免缓冲区溢出
   - 使用 `max_lines` 参数控制输出量
   - 对于大量输出，分批获取

4. **会话清理**:
   - 及时终止不需要的会话
   - 避免长时间保持空闲会话
   - 连接断开时会自动清理相关会话

5. **错误处理**:
   - 检查会话状态，处理会话异常终止
   - 对于需要密码的命令，准备好凭据
   - 处理命令执行超时情况

### 🏷️ 标签过滤示例

1. **查看所有生产环境连接**:
```json
{
  "name": "ssh_list_config",
  "arguments": {
    "filter_tag": "production"
  }
}
```

2. **查看所有开发环境连接**:
```json
{
  "name": "ssh_list_config",
  "arguments": {
    "filter_tag": "development"
  }
}
```

## 🔗 连接ID格式

连接ID格式为: `username@host:port`
例如: `admin@prod.example.com:22`

## 📦 打包和分发

### 创建分发包

```bash
# 构建所有包格式
python build.py --all

# 仅构建wheel包
python build.py --wheel

# 仅创建便携式包
python build.py --portable
```

### 便携式包使用

1. 下载 `ssh-agent-mcp-portable.zip`
2. 解压到目标目录
3. 安装依赖: `pip install -r requirements.txt`
4. 配置SSH连接: 复制并编辑 `ssh_config.json`
5. 启动服务: `python start_ssh_agent.py`

## 安全注意事项

- 请确保SSH凭据的安全，避免在日志中暴露敏感信息
- 建议使用私钥认证而非密码认证
- 在生产环境中考虑使用SSH代理转发
- 定期轮换SSH密钥和密码

## 错误处理

服务包含完善的错误处理机制：
- 连接失败时会返回详细的错误信息
- 命令执行失败时会返回退出码和错误输出
- 支持连接超时和命令执行超时

## 测试

运行测试脚本验证功能：

### 基础功能测试
```bash
python simple_test.py
```

### MCP协议测试
```bash
python test_mcp.py
```

### 交互式命令测试
```bash
# 测试SSH Manager的交互式功能
python test_interactive.py

# 测试MCP交互式工具
python test_mcp_interactive.py
```

## 📁 项目结构

```
sshagent/
├── main.py              # 主入口文件
├── mcp_server.py        # MCP服务器实现
├── ssh_manager.py       # SSH连接管理器
├── config_loader.py     # 配置文件加载器
├── install.py           # 安装脚本
├── build.py             # 打包脚本
├── pyproject.toml       # 项目配置
├── README.md            # 说明文档
├── simple_test.py       # 简单测试脚本
├── test_mcp.py          # MCP协议测试
├── test_interactive.py  # 交互式命令测试脚本
├── test_mcp_interactive.py # MCP交互式工具测试
└── ssh_config.json      # SSH连接配置文件（用户创建）
```

## 📚 依赖项

- `mcp`: Model Context Protocol实现
- `paramiko`: SSH客户端库
- `pydantic`: 数据验证和序列化
- `asyncio`: 异步IO支持

## 🔧 Claude Desktop配置

### 配置文件位置

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`
- **Linux**: `~/.config/claude-desktop/claude_desktop_config.json`

### 基本配置示例

```json
{
  "mcpServers": {
    "ssh-mcp": {
      "command": "uvx",
      "args": [
        "ssh-agent-mcp@latest",
        "--host=192.168.1.100",
        "--user=root",
        "--password=your_password"
      ]
    }
  }
}
```

### 多服务器配置

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
        "--host=192.168.1.200",
        "--user=dev",
        "--password=dev_password"
      ]
    }
  }
}
```

### 配置说明

- `uvx`: Python包运行器，会自动下载并运行指定版本的包
- `ssh-agent-mcp@latest`: 使用最新版本，也可以指定具体版本如 `@0.1.0`
- 命令行参数会覆盖配置文件中的相应设置
- 使用 `--auto-connect` 可以在启动时自动建立SSH连接

### 更多配置示例

查看 `claude_desktop_config_examples.json` 文件获取更多配置示例。

### 📁 SFTP文件传输示例

**1. 上传文件到远程服务器**:
```json
{
  "name": "ssh_upload_file",
  "arguments": {
    "connection_id": "user@server:22",
    "local_path": "/home/user/documents/report.pdf",
    "remote_path": "/remote/uploads/report.pdf"
  }
}
```

**2. 从远程服务器下载文件**:
```json
{
  "name": "ssh_download_file",
  "arguments": {
    "connection_id": "user@server:22",
    "remote_path": "/remote/data/backup.zip",
    "local_path": "/home/user/downloads/backup.zip"
  }
}
```

**3. 浏览远程目录**:
```json
{
  "name": "ssh_list_remote_directory",
  "arguments": {
    "connection_id": "user@server:22",
    "remote_path": "/home/user/documents"
  }
}
```

**4. 创建远程目录**:
```json
{
  "name": "ssh_create_remote_directory",
  "arguments": {
    "connection_id": "user@server:22",
    "remote_path": "/remote/new/project",
    "mode": 755,
    "parents": true
  }
}
```

**5. 批量文件操作工作流**:
```json
// 1. 创建远程目录
{
  "name": "ssh_create_remote_directory",
  "arguments": {
    "connection_id": "user@server:22",
    "remote_path": "/remote/backup/2024-01-15"
  }
}

// 2. 上传多个文件
{
  "name": "ssh_upload_file",
  "arguments": {
    "connection_id": "user@server:22",
    "local_path": "/home/user/data/file1.txt",
    "remote_path": "/remote/backup/2024-01-15/file1.txt"
  }
}

// 3. 列出上传的文件
{
  "name": "ssh_list_remote_directory",
  "arguments": {
    "connection_id": "user@server:22",
    "remote_path": "/remote/backup/2024-01-15"
  }
}
```

**6. 远程文件管理**:
```json
// 获取文件信息
{
  "name": "ssh_get_remote_file_info",
  "arguments": {
    "connection_id": "user@server:22",
    "remote_path": "/remote/logs/app.log"
  }
}

// 重命名文件
{
  "name": "ssh_rename_remote_path",
  "arguments": {
    "connection_id": "user@server:22",
    "old_path": "/remote/logs/app.log",
    "new_path": "/remote/logs/app_backup.log"
  }
}

// 删除旧文件
{
  "name": "ssh_remove_remote_file",
  "arguments": {
    "connection_id": "user@server:22",
    "remote_path": "/remote/logs/old_app.log"
  }
}
```

## 🚨 安全注意事项

- 🔐 请确保SSH凭据的安全，避免在日志中暴露敏感信息
- 🔑 建议使用私钥认证而非密码认证
- 🛡️ 在生产环境中考虑使用SSH代理转发
- 🔄 定期轮换SSH密钥和密码
- 📝 不要将包含密码的配置文件提交到版本控制系统

## 🐛 故障排除

### 常见问题

1. **连接失败**
   - 检查SSH服务器地址和端口
   - 验证用户名和密码/私钥
   - 确认SSH服务正在运行

2. **私钥认证失败**
   - 检查私钥文件路径
   - 确认私钥权限正确（600）
   - 如果私钥有密码，请提供private_key_password

3. **配置文件错误**
   - 验证JSON格式是否正确
   - 检查必需字段是否填写
   - 查看日志获取详细错误信息

4. **MCP服务器无法启动**
   - 检查Python环境和依赖
   - 确认配置文件路径正确
   - 查看错误日志

### 调试模式

设置环境变量启用调试日志：
```bash
export SSH_LOG_LEVEL=DEBUG
python main.py
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License
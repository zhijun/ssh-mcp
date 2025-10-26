# SSH Agent MCP

[中文文档 README_CN.md](README_CN.md)

SSH Agent MCP is a Python-based MCP (Model Context Protocol) stdio server that lets AI assistants manage SSH connections, execute commands, and transfer files over SFTP. It supports both CLI-only configuration and JSON-based connection management, making it easy to operate multiple remote servers securely.

## Features

- uvx support: run via `uvx ssh-agent-mcp` without local install
- CLI arguments: fully configurable via CLI, no config file required
- JSON config: manage multiple SSH connections in a simple JSON file
- Stateful connection management: track and manage multiple concurrent SSH sessions
- Multiple authentication methods: password, private key, and SSH Agent
- Command execution: run commands on remote servers and capture output
- Async commands: support long-running commands (e.g., `top`, `tail`) with live streaming
- Interactive commands: handle interactive programs (e.g., `sudo`, `vim`, `mysql`, `python`)
- Command lifecycle: start, monitor, terminate, and cleanup async/interactive sessions
- Connection status: query and manage connection states in real time
- Auto connect: optionally auto-connect to specified servers on startup
- SFTP file transfer: upload, download, and directory operations
- Remote file management: browse, create, delete, and rename remote files and directories

## Quick Start

### Option 1: Run via uvx (Recommended)

Add this to Claude Desktop config:

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

Restart Claude Desktop and you're ready.

New: zero-argument startup

You can start the MCP server without any SSH parameters and let the assistant provide them dynamically:

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

Then connect using `ssh_connect` or `ssh_connect_by_name` tools.

### Option 2: Local install

```bash
pip install ssh-agent-mcp
# or from source
git clone https://github.com/zhijun/ssh-mcp.git
cd sshagent
pip install -e .
```

### Option 3: Use a JSON config file

1) Create `ssh_config.json`:

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

2) Reference it in Claude Desktop:

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

## Usage Modes

- Zero-argument startup (recommended): let the assistant manage connections dynamically.
- CLI-only mode: pass all connection parameters via CLI.
- Config file mode: manage multiple connections via JSON.
- Private key auth: use `--key` or `--private-key` with optional `--key-password`.

## CLI Arguments

| Argument | Description | Required | Example |
|---------|-------------|----------|---------|
| `--host` | SSH host | optional* | `192.168.1.100` |
| `--user`, `--username` | SSH username | optional* | `root` |
| `--port` | SSH port | optional | `22` |
| `--password` | SSH password | optional | `your_password` |
| `--key`, `--private-key` | private key path | optional | `/home/user/.ssh/id_rsa` |
| `--key-password`, `--private-key-password` | key password | optional | `key_password` |
| `--config`, `-c` | config file path | optional | `/path/to/config.json` |
| `--connection` | connection name | optional | `production-server` |
| `--timeout` | command timeout (ms) | optional | `30000` |
| `--max-chars` | max output chars | optional | `none` |
| `--log-level` | log level | optional | `INFO` |
| `--auto-connect` | auto connect on startup | optional | - |

Note:
- `*` marked parameters are not required in zero-argument or config modes.

## Config File Schema

When using a config file `ssh_config.json`:

```json
{
  "connections": [
    {
      "name": "production-server",
      "host": "prod.example.com",
      "username": "admin",
      "port": 22,
      "private_key": "/home/user/.ssh/id_rsa",
      "description": "Production server",
      "tags": ["production", "critical"]
    },
    {
      "name": "dev-server",
      "host": "dev.example.com",
      "username": "dev",
      "port": 22,
      "private_key": "/home/user/.ssh/id_rsa",
      "description": "Development server",
      "tags": ["development"]
    }
  ],
  "auto_connect": ["production-server"]
}
```

## Tools Overview (MCP)

The server exposes tools for the assistant:

- Connection management: `ssh_connect`, `ssh_connect_by_name`, `ssh_disconnect`, `ssh_list_connections`
- Command execution: `ssh_execute`, `ssh_execute_interactive`, `ssh_execute_async`
- Async/interactive lifecycle: `ssh_check_status`, `ssh_terminate`, `ssh_list_async`
- SFTP operations: `sftp_upload`, `sftp_download`, `sftp_list`, `sftp_mkdir`, `sftp_remove`, `sftp_rename`
- Remote file system: `remote_read_file`, `remote_write_file`
- Status query: `ssh_status`

## Running the Server

```bash
# Via CLI
ssh-agent-mcp --host HOST --user USER --password PASS

# With a config file
ssh-agent-mcp --config /path/to/ssh_config.json --connection production-server

# Zero-argument startup
ssh-agent-mcp
```

## Installation Notes

- Prefer `uvx ssh-agent-mcp@latest` for easy usage.
- When installing via `pip`, specify PyPI to avoid cached mirrors:
  - `pip install -i https://pypi.org/simple ssh-agent-mcp`
- For externally-managed environments, use a virtualenv or `pipx`:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pipx install ssh-agent-mcp`

## Project Links

- Repository: https://github.com/zhijun/ssh-mcp
- Issues: https://github.com/zhijun/ssh-mcp/issues
- PyPI: https://pypi.org/project/ssh-agent-mcp/

## License

MIT License.
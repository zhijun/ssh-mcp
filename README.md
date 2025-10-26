# SSH Agent MCP

[中文文档 README_CN.md](README_CN.md)

Manage SSH and SFTP via MCP tools for AI assistants.

SSH Agent MCP is a Python-based MCP (Model Context Protocol) stdio server that lets AI assistants manage SSH connections, execute commands, and transfer files via SFTP. It supports zero-argument startup, pure CLI configuration, and JSON config files, making it simple to operate multiple remote servers securely.

- Requires: Python >= 3.12
- Project status: Beta

## Why uvx?

- No local install: run `uvx ssh-agent-mcp@latest` directly
- Always up-to-date: pin to `@latest` for consistent versioning
- Ideal for desktop assistants: simplest setup for Claude Desktop

## Install

- Recommended (no local install): `uvx ssh-agent-mcp@latest`
- Pip (use PyPI to avoid cached mirrors): `pip install -i https://pypi.org/simple ssh-agent-mcp`
- Externally managed environments: use virtualenv or pipx
  - `python -m venv .venv && source .venv/bin/activate`
  - `pipx install ssh-agent-mcp`

## Quick Start

### Run via uvx (Claude Desktop)

Minimal config:

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

The assistant can then connect using `ssh_connect` or `ssh_connect_by_name`.

### CLI examples

- Zero-argument startup: `ssh-agent-mcp`
- Direct params: `ssh-agent-mcp --host example.com --user admin --password secret`
- With config file: `ssh-agent-mcp --config /path/to/ssh_config.json --connection production`

### Minimal config file

`ssh_config.json`:

```json
{
  "connections": [
    {
      "name": "production",
      "host": "prod.example.com",
      "username": "admin",
      "private_key": "/home/user/.ssh/id_rsa"
    }
  ],
  "auto_connect": ["production"]
}
```

## Tools (MCP)

- Connection: `ssh_connect`, `ssh_connect_by_name`, `ssh_disconnect`, `ssh_list_connections`
- Commands: `ssh_execute`, `ssh_execute_interactive`, `ssh_execute_async`
- Lifecycle: `ssh_check_status`, `ssh_terminate`, `ssh_list_async`
- SFTP: `sftp_upload`, `sftp_download`, `sftp_list`, `sftp_mkdir`, `sftp_remove`, `sftp_rename`
- Files: `remote_read_file`, `remote_write_file`
- Status: `ssh_status`

## Example: Connect and Execute

```json
{
  "tool": "ssh_connect",
  "params": {
    "name": "prod",
    "host": "prod.example.com",
    "username": "admin",
    "private_key": "/home/user/.ssh/id_rsa"
  }
}
```

```json
{
  "tool": "ssh_execute",
  "params": {
    "connection": "prod",
    "command": "uname -a"
  }
}
```

## Notes

- Prefer `uvx ssh-agent-mcp@latest` for frictionless use.
- If domestic mirrors cache old versions, specify PyPI index explicitly.
- For full CLI options and advanced usage, see the Chinese guide: `README_CN.md`.

## Badges & Links

- Repository: https://github.com/zhijun/ssh-mcp
- Issues: https://github.com/zhijun/ssh-mcp/issues
- PyPI: https://pypi.org/project/ssh-agent-mcp/

## License

MIT License.
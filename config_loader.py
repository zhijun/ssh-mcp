#!/usr/bin/env python3
"""
配置文件加载器
支持JSON格式的SSH连接配置
"""

import json
import os
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class SSHConnectionConfig(BaseModel):
    """SSH连接配置"""
    name: str = Field(description="连接名称，用于标识")
    host: str = Field(description="SSH服务器主机名或IP地址")
    username: str = Field(description="SSH用户名")
    port: int = Field(default=22, description="SSH端口，默认为22")
    password: Optional[str] = Field(default=None, description="SSH密码")
    private_key: Optional[str] = Field(default=None, description="私钥文件路径")
    private_key_password: Optional[str] = Field(default=None, description="私钥密码")
    description: Optional[str] = Field(default=None, description="连接描述")
    tags: List[str] = Field(default_factory=list, description="标签，用于分类")

class SSHAgentConfig(BaseModel):
    """SSH Agent配置"""
    connections: List[SSHConnectionConfig] = Field(default_factory=list, description="SSH连接列表")
    default_timeout: int = Field(default=30, description="默认命令超时时间（秒）")
    log_level: str = Field(default="INFO", description="日志级别")
    auto_connect: List[str] = Field(default_factory=list, description="启动时自动连接的连接名称")
    max_connections: int = Field(default=10, description="最大连接数")

class ConfigLoader:
    """配置加载器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为当前目录下的 ssh_config.json
        """
        self.config_path = config_path or os.path.join(os.getcwd(), "ssh_config.json")
        self.config: Optional[SSHAgentConfig] = None
    
    def load_config(self) -> SSHAgentConfig:
        """
        加载配置文件
        
        Returns:
            SSHAgentConfig: 配置对象
            
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
            pydantic.ValidationError: 配置验证失败
        """
        if not os.path.exists(self.config_path):
            logger.info(f"配置文件不存在，创建默认配置: {self.config_path}")
            self.config = self._create_default_config()
            self.save_config()
            return self.config
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.config = SSHAgentConfig(**config_data)
            logger.info(f"配置加载成功: {self.config_path}")
            return self.config
            
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            raise
        except Exception as e:
            logger.error(f"配置加载失败: {e}")
            raise
    
    def save_config(self):
        """保存配置到文件"""
        if not self.config:
            raise ValueError("没有配置可保存")
        
        try:
            config_dict = self.config.model_dump()
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"配置已保存: {self.config_path}")
        except Exception as e:
            logger.error(f"配置保存失败: {e}")
            raise
    
    def _create_default_config(self) -> SSHAgentConfig:
        """创建默认配置"""
        return SSHAgentConfig(
            connections=[
                SSHConnectionConfig(
                    name="example-server",
                    host="192.168.1.100",
                    username="admin",
                    port=22,
                    description="示例服务器配置",
                    tags=["example", "test"]
                )
            ],
            default_timeout=30,
            log_level="INFO",
            auto_connect=[],
            max_connections=10
        )
    
    def get_connection_by_name(self, name: str) -> Optional[SSHConnectionConfig]:
        """根据名称获取连接配置"""
        if not self.config:
            return None
        
        for conn in self.config.connections:
            if conn.name == name:
                return conn
        return None
    
    def get_connections_by_tag(self, tag: str) -> List[SSHConnectionConfig]:
        """根据标签获取连接配置"""
        if not self.config:
            return []
        
        return [conn for conn in self.config.connections if tag in conn.tags]
    
    def list_connection_names(self) -> List[str]:
        """列出所有连接名称"""
        if not self.config:
            return []
        
        return [conn.name for conn in self.config.connections]

def create_example_config_file(path: str = "ssh_config.json"):
    """
    创建示例配置文件
    
    Args:
        path: 配置文件路径
    """
    example_config = {
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
                "name": "development-server",
                "host": "192.168.1.100",
                "username": "dev",
                "port": 22,
                "password": "dev_password",
                "description": "开发环境服务器",
                "tags": ["development", "test"]
            },
            {
                "name": "docker-container",
                "host": "localhost",
                "username": "root",
                "port": 2222,
                "private_key": "/home/user/.ssh/docker_key",
                "private_key_password": "key_password",
                "description": "本地Docker容器",
                "tags": ["docker", "local"]
            }
        ],
        "default_timeout": 30,
        "log_level": "INFO",
        "auto_connect": ["production-server"],
        "max_connections": 10
    }
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(example_config, f, indent=2, ensure_ascii=False)
        print(f"示例配置文件已创建: {path}")
    except Exception as e:
        print(f"创建示例配置文件失败: {e}")

if __name__ == "__main__":
    # 创建示例配置文件
    create_example_config_file()
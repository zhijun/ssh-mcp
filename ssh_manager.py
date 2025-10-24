import paramiko
import asyncio
import uuid
import time
import os
from typing import Dict, Optional, Tuple, List
from enum import Enum
import logging
from dataclasses import dataclass, field
import threading
import queue

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"

class CommandStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"

class InteractiveStatus(Enum):
    ACTIVE = "active"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"

@dataclass
class AsyncCommand:
    command_id: str
    connection_id: str
    command: str
    status: CommandStatus
    start_time: float
    end_time: Optional[float] = None
    exit_code: Optional[int] = None
    stdout_buffer: List[str] = field(default_factory=list)
    stderr_buffer: List[str] = field(default_factory=list)
    process: Optional[paramiko.Channel] = None
    stdout_size: int = 0
    stderr_size: int = 0

@dataclass
class InteractiveSession:
    session_id: str
    connection_id: str
    initial_command: str
    status: InteractiveStatus
    start_time: float
    end_time: Optional[float] = None
    channel: Optional[paramiko.Channel] = None
    output_buffer: List[str] = field(default_factory=list)
    output_size: int = 0
    last_output_time: float = field(default_factory=time.time)
    pty_width: int = 80
    pty_height: int = 24
    
    def add_output(self, data: str):
        """添加输出数据到缓冲区"""
        self.output_buffer.append(data)
        self.output_size += len(data)
        self.last_output_time = time.time()
        
        # 限制缓冲区大小，保留最近的输出
        max_buffer_size = 100000  # 100KB
        if self.output_size > max_buffer_size:
            # 移除旧的输出，保留最近的50KB
            target_size = max_buffer_size // 2
            removed_size = 0
            while self.output_buffer and removed_size < (self.output_size - target_size):
                removed_data = self.output_buffer.pop(0)
                removed_size += len(removed_data)
            self.output_size -= removed_size

class SSHConnection:
    def __init__(self, host: str, username: str, port: int = 22):
        self.host = host
        self.username = username
        self.port = port
        self.client: Optional[paramiko.SSHClient] = None
        self.status = ConnectionStatus.DISCONNECTED
        self.error_message: Optional[str] = None
        
    async def connect(self, password: Optional[str] = None, 
                     private_key: Optional[str] = None,
                     private_key_password: Optional[str] = None) -> bool:
        """建立SSH连接"""
        try:
            self.status = ConnectionStatus.CONNECTING
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 准备认证信息
            auth_kwargs = {
                'hostname': self.host,
                'port': self.port,
                'username': self.username,
                'timeout': 10
            }
            
            if private_key:
                # 使用私钥认证
                key_obj = paramiko.RSAKey.from_private_key_file(
                    private_key, password=private_key_password
                ) if isinstance(private_key, str) else paramiko.RSAKey.from_private_key(
                    private_key, password=private_key_password
                )
                auth_kwargs['pkey'] = key_obj
            elif password:
                # 使用密码认证
                auth_kwargs['password'] = password
            else:
                # 尝试使用默认SSH agent
                auth_kwargs['look_for_keys'] = True
                auth_kwargs['allow_agent'] = True
            
            # 在线程池中执行连接（因为paramiko是同步的）
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.client.connect(**auth_kwargs))
            
            # 启用keep-alive
            transport = self.client.get_transport()
            if transport:
                # 启用TCP keep-alive
                transport.set_keepalive(60)  # 60秒间隔
                # 设置压缩
                transport.use_compression(True)
                logger.debug(f"已启用SSH keep-alive: {self.username}@{self.host}:{self.port}")
            
            self.status = ConnectionStatus.CONNECTED
            self.error_message = None
            logger.info(f"SSH连接成功: {self.username}@{self.host}:{self.port}")
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.error_message = str(e)
            logger.error(f"SSH连接失败: {e}")
            return False
    
    async def connect_from_config(self, config_host: str,
                                username: Optional[str] = None,
                                password: Optional[str] = None,
                                private_key: Optional[str] = None,
                                private_key_password: Optional[str] = None) -> bool:
        """使用SSH config中的主机名建立连接"""
        try:
            self.status = ConnectionStatus.CONNECTING
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # 加载SSH配置文件
            ssh_config = paramiko.SSHConfig()
            try:
                with open(os.path.expanduser('~/.ssh/config'), 'r') as f:
                    ssh_config.parse(f)
            except FileNotFoundError:
                logger.warning("~/.ssh/config 文件不存在")
                # 如果config文件不存在，回退到普通连接方式
                return await self.connect(password, private_key, private_key_password)
            
            # 获取主机配置
            host_config = ssh_config.lookup(config_host)
            
            # 准备连接参数
            auth_kwargs = {
                'hostname': host_config.get('hostname', config_host),
                'port': int(host_config.get('port', 22)),
                'username': username or host_config.get('user', self.username),
                'timeout': 10
            }
            
            # 更新连接对象的属性
            self.host = auth_kwargs['hostname']
            self.port = auth_kwargs['port']
            self.username = auth_kwargs['username']
            
            # 处理私钥
            if private_key:
                # 使用显式提供的私钥
                try:
                    key_obj = paramiko.RSAKey.from_private_key_file(
                        private_key, password=private_key_password
                    ) if isinstance(private_key, str) else paramiko.RSAKey.from_private_key(
                        private_key, password=private_key_password
                    )
                    auth_kwargs['pkey'] = key_obj
                except Exception as e:
                    logger.error(f"无法加载提供的私钥文件 {private_key}: {e}")
                    # 如果提供的私钥加载失败，继续尝试其他认证方式
            elif 'identityfile' in host_config:
                # 使用config中指定的私钥文件
                identity_file = host_config['identityfile']
                if isinstance(identity_file, list):
                    identity_file = identity_file[0]
                identity_file = os.path.expanduser(identity_file)
                
                try:
                    # 检查文件是否存在
                    if os.path.exists(identity_file):
                        key_obj = paramiko.RSAKey.from_private_key_file(
                            identity_file, password=private_key_password
                        )
                        auth_kwargs['pkey'] = key_obj
                        logger.debug(f"成功加载私钥文件: {identity_file}")
                    else:
                        logger.warning(f"私钥文件不存在: {identity_file}")
                except Exception as e:
                    logger.warning(f"无法加载私钥文件 {identity_file}: {e}")
                    # 如果私钥加载失败，继续尝试其他认证方式
            
            # 如果没有设置私钥，尝试其他认证方式
            if 'pkey' not in auth_kwargs:
                if password:
                    # 使用密码认证
                    auth_kwargs['password'] = password
                else:
                    # 尝试使用默认SSH agent和密钥
                    auth_kwargs['look_for_keys'] = True
                    auth_kwargs['allow_agent'] = True
            
            # 在线程池中执行连接
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self.client.connect(**auth_kwargs))
            
            # 启用keep-alive
            transport = self.client.get_transport()
            if transport:
                # 启用TCP keep-alive
                transport.set_keepalive(60)  # 60秒间隔
                # 设置压缩
                transport.use_compression(True)
                logger.debug(f"已启用SSH keep-alive: {self.username}@{self.host}:{self.port}")
            
            self.status = ConnectionStatus.CONNECTED
            self.error_message = None
            logger.info(f"SSH config连接成功: {self.username}@{self.host}:{self.port} (config: {config_host})")
            return True
            
        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.error_message = str(e)
            logger.error(f"SSH config连接失败: {e}")
            return False
    
    async def disconnect(self):
        """断开SSH连接"""
        if self.client:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self.client.close)
            except Exception as e:
                logger.error(f"断开连接时出错: {e}")
            finally:
                self.client = None
                self.status = ConnectionStatus.DISCONNECTED
                self.error_message = None
    
    async def is_healthy(self) -> bool:
        """检查连接是否健康"""
        if not self.client or self.status != ConnectionStatus.CONNECTED:
            return False
        
        try:
            # 检查传输层状态
            loop = asyncio.get_event_loop()
            transport = await loop.run_in_executor(None, lambda: self.client.get_transport())
            if not transport or not transport.is_active():
                self.status = ConnectionStatus.ERROR
                self.error_message = "SSH传输层不活跃"
                return False
            
            # 执行轻量级命令进行健康检查（使用echo避免输出过多）
            try:
                stdin, stdout, stderr = await loop.run_in_executor(
                    None, lambda: self.client.exec_command('echo "health_check"', timeout=5)
                )
                # 读取输出以确认命令执行成功
                await loop.run_in_executor(None, stdout.read)
                return True
            except Exception as cmd_error:
                # 如果命令执行失败，可能是连接问题，但不立即标记为错误
                logger.debug(f"健康检查命令执行失败: {cmd_error}")
                # 再次检查传输状态
                if transport.is_active():
                    return True  # 传输仍然活跃，认为连接正常
                else:
                    self.status = ConnectionStatus.ERROR
                    self.error_message = f"连接意外断开: {str(cmd_error)}"
                    return False
                    
        except Exception as e:
            logger.warning(f"连接健康检查失败: {e}")
            self.status = ConnectionStatus.ERROR
            self.error_message = f"连接意外断开: {str(e)}"
            return False
    
    async def send_keepalive(self) -> bool:
        """发送keep-alive信号"""
        if not self.client or self.status != ConnectionStatus.CONNECTED:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            transport = await loop.run_in_executor(None, lambda: self.client.get_transport())
            if transport and transport.is_active():
                # 发送keep-alive包
                await loop.run_in_executor(None, transport.send_ignore)
                return True
        except Exception as e:
            logger.debug(f"发送keep-alive失败: {e}")
            self.status = ConnectionStatus.ERROR
            self.error_message = f"连接断开: {str(e)}"
        
        return False
    
    async def execute_command(self, command: str, timeout: int = 30) -> Tuple[int, str, str]:
        """执行SSH命令并返回退出码、stdout、stderr"""
        if not self.client or self.status != ConnectionStatus.CONNECTED:
            return -1, "", "SSH连接未建立"
        
        try:
            # 在执行命令前检查连接健康状态
            if not await self.is_healthy():
                return -1, "", "SSH连接已断开"
            
            loop = asyncio.get_event_loop()
            stdin, stdout, stderr = await loop.run_in_executor(
                None, lambda: self.client.exec_command(command, timeout=timeout)
            )
            
            # 读取输出
            stdout_data = await loop.run_in_executor(None, stdout.read)
            stderr_data = await loop.run_in_executor(None, stderr.read)
            exit_code = stdout.channel.recv_exit_status()
            
            return (
                exit_code,
                stdout_data.decode('utf-8', errors='replace'),
                stderr_data.decode('utf-8', errors='replace')
            )
            
        except Exception as e:
            error_msg = f"命令执行失败: {str(e)}"
            logger.error(error_msg)
            # 检查是否是连接断开导致的错误
            if "Broken pipe" in str(e) or "Connection reset" in str(e) or "Socket is closed" in str(e):
                self.status = ConnectionStatus.ERROR
                self.error_message = f"连接意外断开: {str(e)}"
            return -1, "", error_msg

class SSHManager:
    def __init__(self):
        self.connections: Dict[str, SSHConnection] = {}
        self.async_commands: Dict[str, AsyncCommand] = {}
        self.interactive_sessions: Dict[str, InteractiveSession] = {}
        self._output_monitor_task: Optional[asyncio.Task] = None
        self._interactive_monitor_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._keepalive_task: Optional[asyncio.Task] = None
        self._running = True
        
    def generate_connection_id(self, host: str, username: str, port: int) -> str:
        """生成连接ID"""
        return f"{username}@{host}:{port}"
    
    async def create_connection(self, host: str, username: str, port: int = 22,
                              password: Optional[str] = None,
                              private_key: Optional[str] = None,
                              private_key_password: Optional[str] = None) -> str:
        """创建新的SSH连接"""
        connection_id = self.generate_connection_id(host, username, port)
        
        # 如果连接已存在，先断开
        if connection_id in self.connections:
            await self.connections[connection_id].disconnect()
        
        # 创建新连接
        connection = SSHConnection(host, username, port)
        success = await connection.connect(password, private_key, private_key_password)
        
        # 无论连接成功与否，都将连接对象保存（用于查询错误状态）
        self.connections[connection_id] = connection
        
        if success:
            logger.info(f"SSH连接建立成功: {connection_id}")
            return connection_id
        else:
            logger.warning(f"SSH连接失败: {connection_id}, 错误: {connection.error_message}")
            # 不抛出异常，返回连接ID，让调用者检查状态
            return connection_id
    
    async def create_connection_from_config(self, config_host: str, 
                                          username: Optional[str] = None,
                                          password: Optional[str] = None,
                                          private_key: Optional[str] = None,
                                          private_key_password: Optional[str] = None) -> str:
        """使用SSH config中的主机名创建连接
        
        Args:
            config_host: SSH config中的主机名
            username: 可选的用户名，如果提供将覆盖config中的设置
            password: 可选的密码
            private_key: 可选的私钥文件路径
            private_key_password: 可选的私钥密码
            
        Returns:
            连接ID
        """
        # 首先检查SSH config文件是否存在该主机配置
        try:
            ssh_config = paramiko.SSHConfig()
            config_path = os.path.expanduser('~/.ssh/config')
            with open(config_path, 'r') as f:
                ssh_config.parse(f)
            
            host_config = ssh_config.lookup(config_host)
            if not host_config or host_config.get('hostname') == config_host:
                # 如果没有找到配置或者hostname就是主机名本身，说明配置不存在
                logger.warning(f"SSH config中未找到主机 '{config_host}' 的配置")
                # 使用传入的主机名作为fallback
                actual_hostname = config_host
                actual_username = username or "config_user"
                actual_port = 22
            else:
                # 使用config中的配置
                actual_hostname = host_config.get('hostname', config_host)
                actual_username = username or host_config.get('user', 'config_user')
                actual_port = int(host_config.get('port', 22))
                
        except FileNotFoundError:
            logger.warning("~/.ssh/config 文件不存在，使用主机名作为直接连接")
            actual_hostname = config_host
            actual_username = username or "config_user"
            actual_port = 22
        except Exception as e:
            logger.error(f"解析SSH config时出错: {e}")
            actual_hostname = config_host
            actual_username = username or "config_user"
            actual_port = 22
        
        # 生成连接ID
        connection_id = f"{actual_username}@{actual_hostname}:{actual_port}"
        
        # 如果连接已存在，先断开
        if connection_id in self.connections:
            await self.connections[connection_id].disconnect()
        
        # 创建新连接
        connection = SSHConnection(actual_hostname, actual_username, actual_port)
        
        # 对于config连接，我们让SSH客户端自己处理配置解析
        # 只传递明确的认证参数
        success = await connection.connect_from_config(
            config_host=config_host,
            username=username,
            password=password,
            private_key=private_key,
            private_key_password=private_key_password
        )
        
        # 无论连接成功与否，都将连接对象保存（用于查询错误状态）
        self.connections[connection_id] = connection
        
        if success:
            logger.info(f"SSH config连接建立成功: {connection_id}")
            return connection_id
        else:
            logger.warning(f"SSH config连接失败: {connection_id}, 错误: {connection.error_message}")
            return connection_id
    
    async def get_connection_status(self, connection_id: str) -> Dict:
        """获取连接状态"""
        if connection_id not in self.connections:
            return {
                "status": "not_found",
                "message": "连接不存在"
            }
        
        connection = self.connections[connection_id]
        return {
            "status": connection.status.value,
            "host": connection.host,
            "username": connection.username,
            "port": connection.port,
            "error_message": connection.error_message
        }
    
    async def list_connections(self) -> Dict[str, Dict]:
        """列出所有连接及其状态"""
        result = {}
        for conn_id, connection in self.connections.items():
            result[conn_id] = {
                "status": connection.status.value,
                "host": connection.host,
                "username": connection.username,
                "port": connection.port,
                "error_message": connection.error_message
            }
        return result
    
    async def disconnect(self, connection_id: str) -> bool:
        """断开指定连接"""
        if connection_id not in self.connections:
            return False
        
        await self.connections[connection_id].disconnect()
        del self.connections[connection_id]
        return True
    
    async def execute_command(self, connection_id: str, command: str, 
                            timeout: int = 30) -> Dict:
        """在指定连接上执行命令"""
        if connection_id not in self.connections:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": "连接不存在"
            }
        
        connection = self.connections[connection_id]
        
        # 检查连接状态
        if connection.status != ConnectionStatus.CONNECTED:
            error_msg = connection.error_message or "连接未建立"
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"连接失败: {error_msg}"
            }
        
        try:
            exit_code, stdout, stderr = await connection.execute_command(command, timeout)
            return {
                "success": exit_code == 0,
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr
            }
        except Exception as e:
            return {
                "success": False,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"命令执行失败: {str(e)}"
            }
    
    async def disconnect_all(self):
        """断开所有连接"""
        for connection_id in list(self.connections.keys()):
            await self.disconnect(connection_id)
    
    async def start_async_command(self, connection_id: str, command: str) -> str:
        """启动异步命令执行"""
        if connection_id not in self.connections:
            raise Exception("连接不存在")
        
        connection = self.connections[connection_id]
        if connection.status != ConnectionStatus.CONNECTED:
            raise Exception("连接未建立")
        
        # 生成命令ID
        command_id = str(uuid.uuid4())
        
        # 创建异步命令对象
        async_cmd = AsyncCommand(
            command_id=command_id,
            connection_id=connection_id,
            command=command,
            status=CommandStatus.RUNNING,
            start_time=time.time()
        )
        
        try:
            # 在线程池中执行命令
            loop = asyncio.get_event_loop()
            stdin, stdout, stderr = await loop.run_in_executor(
                None, lambda: connection.client.exec_command(command)
            )
            
            async_cmd.process = stdout.channel
            self.async_commands[command_id] = async_cmd
            
            # 启动输出监控任务
            if self._output_monitor_task is None:
                self._output_monitor_task = asyncio.create_task(self._monitor_command_outputs())
            
            logger.info(f"异步命令已启动: {command_id} ({command})")
            return command_id
            
        except Exception as e:
            async_cmd.status = CommandStatus.FAILED
            async_cmd.end_time = time.time()
            raise Exception(f"启动异步命令失败: {str(e)}")
    
    async def _monitor_command_outputs(self):
        """监控所有运行中命令的输出"""
        while self._running and self.async_commands:
            tasks = []
            for command_id, async_cmd in self.async_commands.items():
                if async_cmd.status == CommandStatus.RUNNING and async_cmd.process:
                    tasks.append(self._collect_command_output(command_id, async_cmd))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            await asyncio.sleep(0.1)  # 每100ms检查一次
    
    async def _collect_command_output(self, command_id: str, async_cmd: AsyncCommand):
        """收集单个命令的输出"""
        try:
            if async_cmd.process and async_cmd.process.recv_ready():
                # 读取stdout
                while async_cmd.process.recv_ready():
                    data = async_cmd.process.recv(4096)
                    if data:
                        text = data.decode('utf-8', errors='replace')
                        async_cmd.stdout_buffer.append(text)
                        async_cmd.stdout_size += len(text)
            
            if async_cmd.process and async_cmd.process.recv_stderr_ready():
                # 读取stderr
                while async_cmd.process.recv_stderr_ready():
                    data = async_cmd.process.recv_stderr(4096)
                    if data:
                        text = data.decode('utf-8', errors='replace')
                        async_cmd.stderr_buffer.append(text)
                        async_cmd.stderr_size += len(text)
            
            # 检查命令是否完成
            if async_cmd.process and async_cmd.process.exit_status_ready():
                exit_code = async_cmd.process.recv_exit_status()
                async_cmd.exit_code = exit_code
                async_cmd.end_time = time.time()
                
                if exit_code == 0:
                    async_cmd.status = CommandStatus.COMPLETED
                else:
                    async_cmd.status = CommandStatus.FAILED
                
                # 读取剩余输出（不再递归调用）
                try:
                    if async_cmd.process.recv_ready():
                        while async_cmd.process.recv_ready():
                            data = async_cmd.process.recv(4096)
                            if data:
                                text = data.decode('utf-8', errors='replace')
                                async_cmd.stdout_buffer.append(text)
                                async_cmd.stdout_size += len(text)
                    
                    if async_cmd.process.recv_stderr_ready():
                        while async_cmd.process.recv_stderr_ready():
                            data = async_cmd.process.recv_stderr(4096)
                            if data:
                                text = data.decode('utf-8', errors='replace')
                                async_cmd.stderr_buffer.append(text)
                                async_cmd.stderr_size += len(text)
                except:
                    pass  # 忽略读取剩余输出时的错误
                
                logger.info(f"异步命令完成: {command_id} (退出码: {exit_code})")
                
        except Exception as e:
            logger.error(f"收集命令输出时出错 {command_id}: {e}")
            async_cmd.status = CommandStatus.FAILED
            async_cmd.end_time = time.time()
    
    async def get_command_status(self, command_id: str) -> Dict:
        """获取异步命令状态和最新输出"""
        if command_id not in self.async_commands:
            return {
                "status": "not_found",
                "message": "命令不存在"
            }
        
        async_cmd = self.async_commands[command_id]
        
        # 手动收集一次最新输出
        if async_cmd.status == CommandStatus.RUNNING:
            await self._collect_command_output(command_id, async_cmd)
        
        return {
            "command_id": command_id,
            "connection_id": async_cmd.connection_id,
            "command": async_cmd.command,
            "status": async_cmd.status.value,
            "start_time": async_cmd.start_time,
            "end_time": async_cmd.end_time,
            "duration": (async_cmd.end_time or time.time()) - async_cmd.start_time,
            "exit_code": async_cmd.exit_code,
            "stdout_size": async_cmd.stdout_size,
            "stderr_size": async_cmd.stderr_size,
            "stdout": "".join(async_cmd.stdout_buffer),
            "stderr": "".join(async_cmd.stderr_buffer)
        }
    
    async def list_async_commands(self) -> Dict[str, Dict]:
        """列出所有异步命令状态"""
        result = {}
        for command_id, async_cmd in self.async_commands.items():
            # 手动收集一次最新输出
            if async_cmd.status == CommandStatus.RUNNING:
                await self._collect_command_output(command_id, async_cmd)
            
            result[command_id] = {
                "connection_id": async_cmd.connection_id,
                "command": async_cmd.command,
                "status": async_cmd.status.value,
                "start_time": async_cmd.start_time,
                "duration": (async_cmd.end_time or time.time()) - async_cmd.start_time,
                "exit_code": async_cmd.exit_code,
                "stdout_size": async_cmd.stdout_size,
                "stderr_size": async_cmd.stderr_size
            }
        return result
    
    async def terminate_command(self, command_id: str) -> bool:
        """终止异步命令"""
        if command_id not in self.async_commands:
            return False
        
        async_cmd = self.async_commands[command_id]
        
        try:
            if async_cmd.process:
                # 使用close()方法来终止SSH通道
                async_cmd.process.close()
                async_cmd.status = CommandStatus.TERMINATED
                async_cmd.end_time = time.time()
                logger.info(f"异步命令已终止: {command_id}")
                return True
        except Exception as e:
            logger.error(f"终止命令失败 {command_id}: {e}")
        
        return False
    
    async def cleanup_completed_commands(self, max_age: float = 3600):
        """清理已完成的命令（默认保留1小时）"""
        current_time = time.time()
        to_remove = []
        
        for command_id, async_cmd in self.async_commands.items():
            if (async_cmd.status in [CommandStatus.COMPLETED, CommandStatus.FAILED, CommandStatus.TERMINATED] 
                and async_cmd.end_time 
                and current_time - async_cmd.end_time > max_age):
                to_remove.append(command_id)
        
        for command_id in to_remove:
            del self.async_commands[command_id]
            logger.info(f"清理已完成的命令: {command_id}")
        
        return len(to_remove)
    
    async def start_health_check(self, interval: int = 30):
        """启动连接健康检查任务"""
        if self._health_check_task:
            return
        
        self._health_check_task = asyncio.create_task(self._health_check_loop(interval))
        logger.info("连接健康检查任务已启动")
    
    async def stop_health_check(self):
        """停止连接健康检查任务"""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("连接健康检查任务已停止")
    
    async def start_keepalive(self, interval: int = 120):
        """启动keep-alive任务"""
        if self._keepalive_task:
            return
        
        self._keepalive_task = asyncio.create_task(self._keepalive_loop(interval))
        logger.info("SSH keep-alive任务已启动")
    
    async def stop_keepalive(self):
        """停止keep-alive任务"""
        if self._keepalive_task:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
            self._keepalive_task = None
            logger.info("SSH keep-alive任务已停止")
    
    async def _keepalive_loop(self, interval: int):
        """keep-alive循环"""
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._send_keepalive_to_all_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"keep-alive循环出错: {e}")
    
    async def _send_keepalive_to_all_connections(self):
        """向所有活跃连接发送keep-alive信号"""
        for connection_id, connection in self.connections.items():
            if connection.status == ConnectionStatus.CONNECTED:
                if not await connection.send_keepalive():
                    logger.debug(f"keep-alive失败，连接可能已断开: {connection_id}")
    
    async def _health_check_loop(self, interval: int):
        """健康检查循环"""
        while self._running:
            try:
                await asyncio.sleep(interval)
                await self._check_all_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康检查循环出错: {e}")
    
    async def _check_all_connections(self):
        """检查所有连接的健康状态"""
        disconnected_connections = []
        
        for connection_id, connection in self.connections.items():
            if connection.status == ConnectionStatus.CONNECTED:
                if not await connection.is_healthy():
                    logger.warning(f"检测到连接断开: {connection_id}")
                    disconnected_connections.append(connection_id)
        
        # 清理断开的连接上的异步命令
        for connection_id in disconnected_connections:
            await self._cleanup_commands_on_disconnected_connection(connection_id)
    
    async def _cleanup_commands_on_disconnected_connection(self, connection_id: str):
        """清理断开连接上的异步命令"""
        commands_to_cleanup = []
        
        for command_id, async_cmd in self.async_commands.items():
            if async_cmd.connection_id == connection_id and async_cmd.status == CommandStatus.RUNNING:
                commands_to_cleanup.append(command_id)
        
        for command_id in commands_to_cleanup:
            try:
                # 终止命令
                await self.terminate_command(command_id)
                # 更新命令状态
                if command_id in self.async_commands:
                    self.async_commands[command_id].status = CommandStatus.FAILED
                    self.async_commands[command_id].end_time = time.time()
                    self.async_commands[command_id].exit_code = -1
                logger.info(f"已清理断开连接上的命令: {command_id}")
            except Exception as e:
                logger.error(f"清理命令失败 {command_id}: {e}")
    
    async def shutdown(self):
        """关闭SSH管理器"""
        logger.info("正在关闭SSH管理器...")
        self._running = False
        
        # 停止所有监控任务
        if self._output_monitor_task:
            self._output_monitor_task.cancel()
            try:
                await self._output_monitor_task
            except asyncio.CancelledError:
                pass
        
        if self._interactive_monitor_task:
            self._interactive_monitor_task.cancel()
            try:
                await self._interactive_monitor_task
            except asyncio.CancelledError:
                pass
        
        await self.stop_health_check()
        await self.stop_keepalive()
        
        # 终止所有异步命令
        for command_id in list(self.async_commands.keys()):
            await self.terminate_command(command_id)
        
        # 终止所有交互式会话
        for session_id in list(self.interactive_sessions.keys()):
            await self.terminate_interactive_session(session_id)
        
        # 断开所有连接
        await self.disconnect_all()

    # ==================== 交互式会话管理 ====================
    
    async def start_interactive_session(self, connection_id: str, command: str = None, 
                                      pty_width: int = 80, pty_height: int = 24) -> str:
        """启动交互式会话"""
        if connection_id not in self.connections:
            raise Exception("连接不存在")
        
        connection = self.connections[connection_id]
        if connection.status != ConnectionStatus.CONNECTED:
            raise Exception("连接未建立")
        
        # 生成会话ID
        session_id = str(uuid.uuid4())
        
        try:
            # 创建带PTY的channel
            channel = connection.client.invoke_shell(
                term='xterm',
                width=pty_width,
                height=pty_height
            )
            
            # 设置channel为非阻塞模式
            channel.settimeout(0.0)
            
            # 创建交互式会话对象
            session = InteractiveSession(
                session_id=session_id,
                connection_id=connection_id,
                initial_command=command or "shell",
                status=InteractiveStatus.ACTIVE,
                start_time=time.time(),
                channel=channel,
                pty_width=pty_width,
                pty_height=pty_height
            )
            
            self.interactive_sessions[session_id] = session
            
            # 如果提供了初始命令，发送它
            if command:
                await asyncio.sleep(0.5)  # 等待shell准备就绪
                await self.send_input_to_session(session_id, command + '\n')
            
            # 启动交互式会话监控任务
            if self._interactive_monitor_task is None:
                self._interactive_monitor_task = asyncio.create_task(self._monitor_interactive_sessions())
            
            logger.info(f"交互式会话已启动: {session_id} ({command or 'shell'})")
            return session_id
            
        except Exception as e:
            raise Exception(f"启动交互式会话失败: {str(e)}")
    
    async def send_input_to_session(self, session_id: str, input_data: str) -> bool:
        """向交互式会话发送输入"""
        if session_id not in self.interactive_sessions:
            raise Exception("交互式会话不存在")
        
        session = self.interactive_sessions[session_id]
        if session.status not in [InteractiveStatus.ACTIVE, InteractiveStatus.WAITING_INPUT]:
            raise Exception(f"会话状态不允许输入: {session.status.value}")
        
        try:
            if session.channel and not session.channel.closed:
                # 发送输入数据
                session.channel.send(input_data.encode('utf-8'))
                session.status = InteractiveStatus.ACTIVE
                logger.debug(f"向会话 {session_id} 发送输入: {repr(input_data)}")
                return True
            else:
                session.status = InteractiveStatus.FAILED
                raise Exception("会话channel已关闭")
                
        except Exception as e:
            session.status = InteractiveStatus.FAILED
            raise Exception(f"发送输入失败: {str(e)}")
    
    async def get_interactive_output(self, session_id: str, since_time: float = None, 
                                   max_lines: int = None) -> Dict:
        """获取交互式会话输出"""
        if session_id not in self.interactive_sessions:
            return {
                "status": "not_found",
                "message": "交互式会话不存在"
            }
        
        session = self.interactive_sessions[session_id]
        
        # 获取输出数据
        if since_time is not None:
            # 过滤指定时间之后的输出（简化实现，实际可能需要更精确的时间戳）
            output_lines = session.output_buffer[-100:] if session.output_buffer else []
        else:
            output_lines = session.output_buffer
        
        if max_lines and len(output_lines) > max_lines:
            output_lines = output_lines[-max_lines:]
        
        output_text = ''.join(output_lines)
        
        return {
            "status": session.status.value,
            "session_id": session_id,
            "connection_id": session.connection_id,
            "initial_command": session.initial_command,
            "output": output_text,
            "output_size": session.output_size,
            "last_output_time": session.last_output_time,
            "start_time": session.start_time,
            "end_time": session.end_time,
            "duration": (session.end_time or time.time()) - session.start_time,
            "pty_size": f"{session.pty_width}x{session.pty_height}",
            "channel_closed": session.channel.closed if session.channel else True
        }
    
    async def list_interactive_sessions(self) -> Dict[str, Dict]:
        """列出所有交互式会话"""
        result = {}
        for session_id, session in self.interactive_sessions.items():
            result[session_id] = {
                "status": session.status.value,
                "connection_id": session.connection_id,
                "initial_command": session.initial_command,
                "start_time": session.start_time,
                "duration": (session.end_time or time.time()) - session.start_time,
                "output_size": session.output_size,
                "last_output_time": session.last_output_time,
                "pty_size": f"{session.pty_width}x{session.pty_height}"
            }
        return result
    
    async def terminate_interactive_session(self, session_id: str) -> bool:
        """终止交互式会话"""
        if session_id not in self.interactive_sessions:
            return False
        
        session = self.interactive_sessions[session_id]
        
        try:
            if session.channel and not session.channel.closed:
                session.channel.close()
            
            session.status = InteractiveStatus.TERMINATED
            session.end_time = time.time()
            
            logger.info(f"交互式会话已终止: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"终止交互式会话失败: {session_id}, 错误: {str(e)}")
            return False
    
    async def cleanup_interactive_sessions(self, max_age: float = 3600):
        """清理已完成的交互式会话"""
        current_time = time.time()
        sessions_to_cleanup = []
        
        for session_id, session in self.interactive_sessions.items():
            if session.status in [InteractiveStatus.COMPLETED, InteractiveStatus.FAILED, InteractiveStatus.TERMINATED]:
                if session.end_time and (current_time - session.end_time) > max_age:
                    sessions_to_cleanup.append(session_id)
        
        for session_id in sessions_to_cleanup:
            del self.interactive_sessions[session_id]
            logger.info(f"已清理交互式会话: {session_id}")
    
    async def _monitor_interactive_sessions(self):
        """监控所有交互式会话的输出"""
        while self._running and self.interactive_sessions:
            tasks = []
            for session_id, session in self.interactive_sessions.items():
                if session.status == InteractiveStatus.ACTIVE and session.channel:
                    tasks.append(self._collect_interactive_output(session_id, session))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            await asyncio.sleep(0.1)  # 每100ms检查一次
    
    async def _collect_interactive_output(self, session_id: str, session: InteractiveSession):
        """收集单个交互式会话的输出"""
        try:
            if session.channel and not session.channel.closed:
                # 检查是否有数据可读
                if session.channel.recv_ready():
                    data = session.channel.recv(4096)
                    if data:
                        text = data.decode('utf-8', errors='replace')
                        session.add_output(text)
                
                # 检查channel是否已关闭
                if session.channel.exit_status_ready():
                    session.status = InteractiveStatus.COMPLETED
                    session.end_time = time.time()
                    logger.info(f"交互式会话已完成: {session_id}")
                    
        except Exception as e:
            logger.error(f"收集交互式会话输出失败: {session_id}, 错误: {str(e)}")
            session.status = InteractiveStatus.FAILED
            session.end_time = time.time()
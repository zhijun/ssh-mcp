FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY *.py ./
COPY pyproject.toml ./

# 安装Python依赖
RUN pip install --no-cache-dir -e .

# 创建示例配置
RUN python -c "from config_loader import create_example_config_file; create_example_config_file('ssh_config.example.json')"

# 创建非root用户
RUN useradd -m -u 1000 sshagent && chown -R sshagent:sshagent /app
USER sshagent

# 暴露端口（如果需要）
EXPOSE 22

# 设置入口点
ENTRYPOINT ["python", "main.py"]

# 默认命令
CMD []
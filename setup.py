#!/usr/bin/env python3
"""
setup.py for ssh-agent-mcp
"""

from setuptools import setup, find_packages
import pathlib

# 读取README文件
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text(encoding="utf-8")

# 读取pyproject.toml
import tomllib
with open(HERE / "pyproject.toml", "rb") as f:
    pyproject = tomllib.load(f)

setup(
    name=pyproject["project"]["name"],
    version=pyproject["project"]["version"],
    description=pyproject["project"]["description"],
    long_description=README,
    long_description_content_type="text/markdown",
    author=pyproject["project"]["authors"][0]["name"],
    author_email=pyproject["project"]["authors"][0]["email"],
    url=pyproject["project"]["urls"]["Homepage"],
    packages=find_packages(),
    include_package_data=True,
    python_requires=pyproject["project"]["requires-python"],
    install_requires=pyproject["project"]["dependencies"],
    # 新增：将单文件模块包含进来
    py_modules=["main", "mcp_server", "ssh_manager", "config_loader"],
    entry_points={
        "console_scripts": [
            # 修正入口指向同步包装函数
            "ssh-agent-mcp=main:cli",
        ],
    },
    classifiers=pyproject["project"]["classifiers"],
    keywords=pyproject["project"]["keywords"],
    license=pyproject["project"]["license"]["text"],
)
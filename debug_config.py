#!/usr/bin/env python3
"""
调试脚本：检查config对象的实际结构
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_loader import ConfigLoader

def debug_config():
    print("=== 调试配置对象结构 ===")
    
    config_loader = ConfigLoader()
    try:
        config = config_loader.load_config()
        print(f"配置加载成功: {type(config)}")
        print(f"配置对象属性: {dir(config)}")
        
        if hasattr(config, 'connections'):
            print(f"config.connections 存在: {len(config.connections)} 个连接")
            for i, conn in enumerate(config.connections):
                print(f"  连接 {i}: {conn.name}")
        else:
            print("config.connections 不存在")
            
        if hasattr(config, 'config'):
            print(f"config.config 存在: {type(config.config)}")
            if hasattr(config.config, 'connections'):
                print(f"config.config.connections 存在: {len(config.config.connections)} 个连接")
        else:
            print("config.config 不存在")
            
    except Exception as e:
        print(f"配置加载失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_config()
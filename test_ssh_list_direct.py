#!/usr/bin/env python3
"""
直接测试ssh_list_config功能
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import handle_call_tool

async def test_ssh_list_config():
    print("=== 测试 ssh_list_config ===")
    
    try:
        result = await handle_call_tool("ssh_list_config", {})
        print(f"测试结果: {result}")
        print(f"是否错误: {result.isError if hasattr(result, 'isError') else 'N/A'}")
        
        if hasattr(result, 'content') and result.content:
            for content in result.content:
                if hasattr(content, 'text'):
                    print(f"内容: {content.text}")
                    
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ssh_list_config())
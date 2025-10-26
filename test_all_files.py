#!/usr/bin/env python3
"""Script to test all test files and identify any failures"""

import subprocess
import sys

test_files = [
    "test_mcp_tools_basic_connections.py",
    "test_mcp_tools_config_management.py", 
    "test_mcp_tools_status_query.py",
    "test_mcp_tools_command_execution.py",
    "test_mcp_tools_async_commands.py",
    "test_mcp_tools_interactive.py",
    "test_mcp_tools_sftp.py"
]

all_passed = True

for test_file in test_files:
    print(f"\n=== Testing {test_file} ===")
    cmd = f"venv/bin/python -m pytest {test_file} -v"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"✓ ALL TESTS PASSED: {test_file}")
        else:
            print(f"✗ TESTS FAILED: {test_file}")
            print(f"Error output:\n{result.stderr}")
            print(f"Standard output:\n{result.stdout}")
            all_passed = False
    except subprocess.TimeoutExpired:
        print(f"✗ TIMEOUT: {test_file}")
        all_passed = False
    except Exception as e:
        print(f"✗ ERROR: {test_file} - {e}")
        all_passed = False

print(f"\n=== FINAL SUMMARY ===")
if all_passed:
    print("🎉 ALL TESTS PASSED! Ready for PyPI submission.")
else:
    print("❌ Some tests failed. Please fix before submitting to PyPI.")
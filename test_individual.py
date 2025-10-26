#!/usr/bin/env python3
"""Script to test each test method individually and identify failures"""

import subprocess
import sys

tests = [
    "test_ssh_connect_success",
    "test_ssh_connect_with_port", 
    "test_ssh_connect_with_private_key",
    "test_ssh_connect_missing_required_params",
    "test_ssh_connect_failure",
    "test_ssh_connect_by_name_success",
    "test_ssh_connect_by_name_not_found",
    "test_ssh_connect_by_name_missing_name",
    "test_ssh_connect_by_config_host_success",
    "test_ssh_connect_by_config_host_missing_host",
    "test_ssh_disconnect_success",
    "test_ssh_disconnect_missing_connection_id",
    "test_ssh_disconnect_failure",
    "test_ssh_disconnect_all_success"
]

failed_tests = []
passed_tests = []

for test in tests:
    cmd = f"venv/bin/python -m pytest test_mcp_tools_basic_connections.py::TestBasicConnectionTools::{test} -v"
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            passed_tests.append(test)
            print(f"✓ PASSED: {test}")
        else:
            failed_tests.append((test, result.stderr + result.stdout))
            print(f"✗ FAILED: {test}")
            print(f"  STDOUT: {result.stdout}")
            print(f"  STDERR: {result.stderr}")
    except subprocess.TimeoutExpired:
        failed_tests.append((test, "TIMEOUT"))
        print(f"✗ TIMEOUT: {test}")
    except Exception as e:
        failed_tests.append((test, str(e)))
        print(f"✗ ERROR: {test} - {e}")

print(f"\n=== SUMMARY ===")
print(f"Passed: {len(passed_tests)}")
print(f"Failed: {len(failed_tests)}")

if failed_tests:
    print(f"\nFailed tests:")
    for test, error in failed_tests:
        print(f"  - {test}: {error[:100]}...")
"""pytest 配置和共享 fixtures"""
import os
import sys
from pathlib import Path

# 添加 scripts 到 path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest


@pytest.fixture
def mock_credentials(monkeypatch):
    """模拟百度网盘凭证"""
    monkeypatch.setenv("BAIDU_BDUSS", "test_bduss_1234567890")
    monkeypatch.setenv("BAIDU_STOKEN", "test_stoken_1234567890")
    monkeypatch.setenv("BAIDU_BAIDUID", "test_baiduid_1234567890")
    return {
        "BAIDU_BDUSS": "test_bduss_1234567890",
        "BAIDU_STOKEN": "test_stoken_1234567890",
        "BAIDU_BAIDUID": "test_baiduid_1234567890",
    }


@pytest.fixture
def temp_upload_file(tmp_path):
    """创建临时上传测试文件"""
    test_file = tmp_path / "test_upload.txt"
    test_file.write_text("Hello Baidu Netdisk!\n" * 100)
    return test_file


@pytest.fixture
def temp_large_file(tmp_path):
    """创建 10MB 临时文件用于上传测试"""
    test_file = tmp_path / "test_large.bin"
    test_file.write_bytes(b"x" * (10 * 1024 * 1024))
    return test_file

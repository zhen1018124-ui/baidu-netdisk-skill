"""baidu_pcs.py 单元测试"""
import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# 导入主模块
from baidu_pcs import (
    BaiduError,
    make_session,
    check_ok,
    get_bdstoken,
    cmd_quota,
    cmd_list,
    cmd_meta,
    cmd_share,
)


class TestBaiduError:
    """BaiduError 异常类测试"""

    def test_baidu_error_creation(self):
        """测试异常创建"""
        err = BaiduError(110, "BDUSS expired")
        assert err.errno == 110
        assert err.msg == "BDUSS expired"
        assert "errno=110" in str(err)

    def test_baidu_error_message_format(self):
        """测试异常消息格式"""
        err = BaiduError(-9, "path not found")
        assert "errno=-9" in str(err)
        assert "path not found" in str(err)

    def test_baidu_error_with_empty_message(self):
        """测试空消息的异常"""
        err = BaiduError(2, "")
        assert err.errno == 2
        assert err.msg == ""


class TestCheckOk:
    """check_ok 函数测试"""

    def test_check_ok_success(self):
        """errno=0 应该通过"""
        data = {"errno": 0, "data": "success"}
        check_ok(data)  # 不抛异常

    def test_check_ok_with_no_errno(self):
        """缺少 errno 字段视为 0，应该通过"""
        data = {"data": "success"}
        check_ok(data)  # errno 默认为 0

    def test_check_ok_raises_on_error(self):
        """errno != 0 应该抛异常"""
        data = {"errno": 110, "errmsg": "BDUSS expired"}
        with pytest.raises(BaiduError) as exc_info:
            check_ok(data)
        assert exc_info.value.errno == 110

    def test_check_ok_with_errortext(self):
        """支持 errortext 字段"""
        data = {"errno": -9, "errortext": "path not found"}
        with pytest.raises(BaiduError) as exc_info:
            check_ok(data)
        assert "path not found" in exc_info.value.msg

    def test_check_ok_various_errno_values(self):
        """测试各种错误码"""
        error_codes = [
            (-1, "UNKNOWN"),
            (2, "PARAM_ERROR"),
            (3, "QUOTA_EXCEEDED"),
            (8, "FILE_EXISTS"),
            (110, "BDUSS_EXPIRED"),
            (403, "STOKEN_MISSING"),
            (500, "SERVER_ERROR"),
        ]
        for errno, msg in error_codes:
            data = {"errno": errno, "errmsg": msg}
            with pytest.raises(BaiduError) as exc_info:
                check_ok(data)
            assert exc_info.value.errno == errno


class TestMakeSession:
    """make_session 函数测试"""

    def test_make_session_with_env_vars(self, mock_credentials):
        """从环境变量读取凭证"""
        session = make_session()
        assert session is not None
        # 验证 Cookie 已设置
        assert session.cookies.get("BDUSS") == "test_bduss_1234567890"
        assert session.cookies.get("STOKEN") == "test_stoken_1234567890"

    def test_make_session_without_bduss_exits(self, monkeypatch):
        """缺少 BDUSS 应该退出"""
        monkeypatch.delenv("BAIDU_BDUSS", raising=False)
        monkeypatch.delenv("BAIDU_STOKEN", raising=False)
        with pytest.raises(SystemExit):
            make_session()

    def test_make_session_headers_set(self, mock_credentials):
        """验证请求头设置"""
        session = make_session()
        assert "User-Agent" in session.headers
        assert "Referer" in session.headers
        assert "https://pan.baidu.com" in session.headers["Referer"]
        assert "Accept" in session.headers
        assert "Accept-Language" in session.headers

    def test_make_session_verbose_mode(self, mock_credentials, capsys):
        """测试详细模式"""
        session = make_session(verbose=True)
        assert session is not None


class TestCmdQuota:
    """cmd_quota 命令测试"""

    @patch("requests.Session.get")
    def test_cmd_quota_success(self, mock_get, mock_credentials):
        """测试查询容量成功"""
        # 模拟 API 响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "total": 5497558138880,  # 5TB
            "used": 1560234567890,   # 1.42TB
        }
        mock_get.return_value = mock_response

        session = make_session()
        args = Mock()

        with patch("builtins.print"):
            result = cmd_quota(args, session)

        assert result == 0
        mock_get.assert_called_once()

    @patch("requests.Session.get")
    def test_cmd_quota_api_error(self, mock_get, mock_credentials):
        """测试 API 返回错误"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "errno": 110,
            "errmsg": "BDUSS expired",
        }
        mock_get.return_value = mock_response

        session = make_session()
        args = Mock()

        with pytest.raises(BaiduError):
            cmd_quota(args, session)


class TestCmdList:
    """cmd_list 命令测试"""

    @patch("requests.Session.get")
    def test_cmd_list_success(self, mock_get, mock_credentials):
        """测试列目录成功"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "list": [
                {
                    "server_filename": "test_file.txt",
                    "isdir": 0,
                    "size": 1024,
                    "server_mtime": 1686398400,
                },
                {
                    "server_filename": "test_dir",
                    "isdir": 1,
                    "size": 0,
                    "server_mtime": 1686398400,
                },
            ],
        }
        mock_get.return_value = mock_response

        session = make_session()
        args = Mock(path="/", page=1, size=100)

        with patch("builtins.print"):
            result = cmd_list(args, session)

        assert result == 0

    @patch("requests.Session.get")
    def test_cmd_list_empty_directory(self, mock_get, mock_credentials):
        """测试列空目录"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "list": [],
        }
        mock_get.return_value = mock_response

        session = make_session()
        args = Mock(path="/empty", page=1, size=100)

        with patch("builtins.print"):
            result = cmd_list(args, session)

        assert result == 0


class TestCmdMeta:
    """cmd_meta 命令测试"""

    @patch("requests.Session.get")
    def test_cmd_meta_success(self, mock_get, mock_credentials):
        """测试元信息查询成功"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "info": [
                {
                    "fs_id": 123456,
                    "path": "/test_file.txt",
                    "server_filename": "test_file.txt",
                    "size": 1024,
                    "isdir": 0,
                    "md5": "abc123def456",
                    "server_mtime": 1686398400,
                    "category": 6,
                }
            ],
        }
        mock_get.return_value = mock_response

        session = make_session()
        args = Mock(path="/test_file.txt")

        with patch("builtins.print"):
            result = cmd_meta(args, session)

        assert result == 0

    @patch("requests.Session.get")
    def test_cmd_meta_not_found(self, mock_get, mock_credentials):
        """测试文件不存在"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "errno": 0,
            "info": [],
        }
        mock_get.return_value = mock_response

        session = make_session()
        args = Mock(path="/nonexistent")

        with patch("builtins.print"):
            result = cmd_meta(args, session)

        assert result == 1


class TestCmdShare:
    """cmd_share 命令测试"""

    @patch("requests.Session.post")
    @patch("requests.Session.get")
    def test_cmd_share_with_code(self, mock_get, mock_post, mock_credentials):
        """测试生成带提取码的分享链接"""
        # 模拟 bdstoken 获取
        bdstoken_response = Mock(
            text='<html>..."bdstoken":"abc123xyz"...</html>'
        )

        # 模拟 meta 查询
        meta_response = Mock()
        meta_response.json.return_value = {
            "errno": 0,
            "info": [{"fs_id": 123456, "path": "/test"}],
        }

        # 模拟分享创建
        share_response = Mock()
        share_response.json.return_value = {
            "errno": 0,
            "link": "https://pan.baidu.com/s/1xxxxx",
            "shareid": 987654,
        }

        mock_get.side_effect = [bdstoken_response, meta_response]
        mock_post.return_value = share_response

        session = make_session()
        args = Mock(path="/test", code="8888", period=0)

        with patch("builtins.print"):
            result = cmd_share(args, session)

        assert result == 0

    @patch("requests.Session.post")
    @patch("requests.Session.get")
    def test_cmd_share_permanent_no_code(self, mock_get, mock_post, mock_credentials):
        """测试生成永久分享链接（无提取码）"""
        bdstoken_response = Mock(
            text='<html>..."bdstoken":"abc123xyz"...</html>'
        )

        meta_response = Mock()
        meta_response.json.return_value = {
            "errno": 0,
            "info": [{"fs_id": 123456}],
        }

        share_response = Mock()
        share_response.json.return_value = {
            "errno": 0,
            "link": "https://pan.baidu.com/s/1xxxxx",
        }

        mock_get.side_effect = [bdstoken_response, meta_response]
        mock_post.return_value = share_response

        session = make_session()
        args = Mock(path="/test", code=None, period=0)

        with patch("builtins.print"):
            result = cmd_share(args, session)

        assert result == 0

    @patch("requests.Session.post")
    @patch("requests.Session.get")
    def test_cmd_share_limited_period(self, mock_get, mock_post, mock_credentials):
        """测试生成限时分享链接"""
        bdstoken_response = Mock(
            text='<html>..."bdstoken":"abc123xyz"...</html>'
        )

        meta_response = Mock()
        meta_response.json.return_value = {
            "errno": 0,
            "info": [{"fs_id": 123456}],
        }

        share_response = Mock()
        share_response.json.return_value = {
            "errno": 0,
            "link": "https://pan.baidu.com/s/1xxxxx",
        }

        mock_get.side_effect = [bdstoken_response, meta_response]
        mock_post.return_value = share_response

        session = make_session()
        args = Mock(path="/test", code="1234", period=7)

        with patch("builtins.print"):
            result = cmd_share(args, session)

        assert result == 0


class TestErrorHandling:
    """错误处理测试"""

    def test_bduss_expired_error(self):
        """测试 BDUSS 过期错误"""
        data = {"errno": 110, "errmsg": "BDUSS expired"}
        with pytest.raises(BaiduError) as exc_info:
            check_ok(data)
        assert exc_info.value.errno == 110

    def test_permission_denied_error(self):
        """测试权限拒绝错误"""
        data = {"errno": -8, "errortext": "Permission denied"}
        with pytest.raises(BaiduError) as exc_info:
            check_ok(data)
        assert exc_info.value.errno == -8

    def test_path_not_found_error(self):
        """测试路径不存在错误"""
        data = {"errno": -9, "errmsg": "Path not found"}
        with pytest.raises(BaiduError) as exc_info:
            check_ok(data)
        assert exc_info.value.errno == -9

    def test_file_exists_error(self):
        """测试文件已存在错误"""
        data = {"errno": 8, "errmsg": "File exists"}
        with pytest.raises(BaiduError) as exc_info:
            check_ok(data)
        assert exc_info.value.errno == 8


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

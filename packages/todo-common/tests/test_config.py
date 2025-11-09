import tempfile
from pathlib import Path
import sys
import os

# Ensure the project root is in sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from todo_common import config

# NOTE: The below tests were written using assistance from GitHub Copilot.


def test_get_config_file_returns_default_when_none_exist(monkeypatch):
    # Use a temp home directory
    with tempfile.TemporaryDirectory() as tmp_home:
        monkeypatch.setenv("HOME", tmp_home)
        # Remove any .todo_client/.todo_server dirs if present
        client_path = Path(tmp_home) / ".todo_client/config.ini"
        server_path = Path(tmp_home) / ".todo_server/config.ini"
        if client_path.exists():
            client_path.unlink()
        if server_path.exists():
            server_path.unlink()
        # Should return the default path (first in list)
        result = config.get_config_file("client")
        assert str(result) == str(client_path)
        result = config.get_config_file("server")
        assert str(result) == str(server_path)


def test_init_config_file_creates_file(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp_home:
        monkeypatch.setenv("HOME", tmp_home)
        config_path = Path(tmp_home) / ".todo_client/config.ini"
        assert not config_path.exists()
        config.init_config_file("client")
        assert config_path.exists()
        with open(config_path) as f:
            content = f.read()
        assert "username=default_user" in content
        assert "server_url=http://localhost:8030" in content
        assert "database_file=todo_client.db" in content


def test_load_config_reads_values(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp_home:
        monkeypatch.setenv("HOME", tmp_home)
        config_path = Path(tmp_home) / ".todo_client/config.ini"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            "username=alice\nserver_url=http://foo\ndatabase_file=bar.db\n"
        )
        loaded = config.load_config("client")
        assert loaded["username"] == "alice"
        assert loaded["server_url"] == "http://foo"
        assert loaded["database_file"] == "bar.db"


def test_load_config_returns_empty_if_missing(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp_home:
        monkeypatch.setenv("HOME", tmp_home)
        loaded = config.load_config("client")
        assert loaded == {}

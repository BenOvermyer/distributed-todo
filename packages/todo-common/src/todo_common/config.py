
from pathlib import Path
import os
import sys



def get_config_file(config_type: str, config_path: str = None) -> Path:
    """
    Determine the config file path.
    If config_path is provided, use it directly.
    Returns:
        Path to config file.
    """
    if config_path:
        return Path(config_path).expanduser()

    if config_type == "client":
        POSSIBLE_PATHS = (
            f"{os.path.expanduser('~')}/.todo_client/config.ini",
            Path(__file__).parent.parent / ".todo_client/config.ini",
            Path(sys.argv[0]).parent / "config.ini",
        )
    else:
        POSSIBLE_PATHS = (
            f"{os.path.expanduser('~')}/.todo_server/config.ini",
            Path(__file__).parent.parent / ".todo_server/config.ini",
            Path(sys.argv[0]).parent / "config.ini",
        )

    for p in POSSIBLE_PATHS:
        path = Path(p).expanduser()
        if path.exists():
            return path

    # Default to first path if none exist
    return Path(POSSIBLE_PATHS[0]).expanduser()


def init_config_file(config_type: str = "client", config_path: str = None) -> None:
    """
    Initialize the config file with default settings if it doesn't exist.
    """
    config_path = get_config_file(config_type, config_path)
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            if config_type == "client":
                f.write("username=default_user\n")
                f.write("server_url=http://localhost:8030\n")
            f.write(f"database_file=todo_{config_type}.db\n")


def load_config(config_type: str, config_path: str = None) -> dict:
    """
    Load configuration from the config file.

    Returns:
        Configuration as a dictionary.
    """
    config_path = get_config_file(config_type, config_path)
    if not config_path.exists():
        return {}

    with open(config_path, "r") as f:
        lines = f.readlines()

    config = {}
    for line in lines:
        if "=" in line:
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()

    return config

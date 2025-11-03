from pathlib import Path
import os

def get_config_file(config_type: str) -> Path:
    """
    Determine the config file path.

    Returns:
        Path to config file.
    """

    if config_type == "client":
        POSSIBLE_PATHS = (
            f"{os.path.expanduser('~')}/.todo_client/config.ini",
            Path(__file__).parent.parent / ".todo_client/config.ini",
        )
    else:
        POSSIBLE_PATHS = (
            f"{os.path.expanduser('~')}/.todo_server/config.ini",
            Path(__file__).parent.parent / ".todo_server/config.ini",
        )

    for p in POSSIBLE_PATHS:
        path = Path(p).expanduser()
        if path.exists():
            return path

    # Default to first path if none exist
    return Path(POSSIBLE_PATHS[0]).expanduser()

def init_config_file(config_type: str = "client") -> None:
    """
    Initialize the config file with default settings if it doesn't exist.
    """
    config_path = get_config_file(config_type)
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            if config_type == "client":
                f.write("username=default_user\n")
                f.write("server_url=http://localhost:9777\n")
            f.write(f"database_file=todo_{config_type}.db\n")

def load_config(config_type: str) -> dict:
    """
    Load configuration from the config file.

    Returns:
        Configuration as a dictionary.
    """
    config_path = get_config_file(config_type)
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
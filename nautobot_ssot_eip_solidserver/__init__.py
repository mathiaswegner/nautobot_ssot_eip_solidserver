import os
import pathlib
from nautobot.apps import NautobotAppConfig


def get_version():
    """get the version with build number

    Returns:
        str: version with build
    """
    version_dir = pathlib.Path(__file__).parent
    try:
        with (version_dir / "_version.py").open("r") as version_file:
            lines = version_file.readlines()
            for line in lines:
                if "__version__" in line:
                    return line.split(" ")[-1].rstrip("'").strip("\n' ")
            return "Build unknown"
    except FileNotFoundError:
        return "Build unknown"


class SSoTEIPSolidServerConfig(NautobotAppConfig):
    name = 'nautobot_ssot_eip_solidserver'
    verbose_name = 'SSoT EIP Solidserver'
    description = \
        'SSoT plugin to synchronize data between Solidserver and Nautobot'
    version = '0.0.5'
    build = get_version()
    author = 'Mathias Wegner'
    author_email = 'mwegner@isc.upenn.edu'
    required_settings = []
    default_settings = {
        "nnn_user": "nautobot_nnn",
        "nnn_url": "https://nnn.upenn.edu",
        "nnn_credential": "/opt/nautobot/bazaar/nautobot_nnn"
    }


config = SSoTEIPSolidServerConfig

"""Application config"""
from importlib.metadata import PackageNotFoundError, version
from typing import Any

from nautobot.apps import NautobotAppConfig  # type: ignore


def get_version():
    """get the version with build number

    Returns:
        str: version with build
    """
    try:
        return version("nautobot-plugin-ssot-eip-solidserver")
    except PackageNotFoundError:
        # package is not installed
        return "Unknown"


class SSoTEIPSolidServerConfig(NautobotAppConfig):
    """Application config"""

    name = "nautobot_plugin_ssot_eip_solidserver"
    verbose_name = "SSoT Plugin for EIP SolidSERVER"
    description = "SSoT plugin to synchronize data between SolidSERVER and Nautobot"
    version = get_version()
    build = get_version()
    author = "Mathias Wegner"
    author_email = "mwegner@isc.upenn.edu"
    required_settings: list[Any] = []
    default_settings = {
        "nnn_user": "nautobot_nnn",
        "nnn_url": "https://nnn.upenn.edu",
        "nnn_credential": "Credential not found!",
    }


config = SSoTEIPSolidServerConfig

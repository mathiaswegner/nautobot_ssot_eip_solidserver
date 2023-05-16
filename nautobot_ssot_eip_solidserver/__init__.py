from nautobot.apps import NautobotAppConfig
from nautobot_ssot_eip_solidserver.utils.ssutils import get_version


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

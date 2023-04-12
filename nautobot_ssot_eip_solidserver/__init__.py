from nautobot.apps import NautobotAppConfig

class SSoTEIPSolidServerConfig(NautobotAppConfig):
    name = 'nautobot_ssot_eip_solidserver'
    verbose_name = 'SSoT EIP Solidserver'
    description = 'SSoT plugin to synchronize data between Solidserver and Nautobot'
    version = '0.0.5'
    author = 'Mathias Wegner'
    author_email = 'mwegner@isc.upenn.edu'
    required_settings = []
    default_settings = {
        'loud': False
    }

config = SSoTEIPSolidServerConfig

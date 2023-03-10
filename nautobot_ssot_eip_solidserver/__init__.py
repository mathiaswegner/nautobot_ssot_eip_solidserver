from nautobot.apps import NautobotAppConfig

class SSoTEIPSolidServerConfig(NautobotAppConfig):
    name = 'nautobot_ssot_eip_solidserver'
    verbose_name = 'SSoT EIP Solidserver'
    description = 'An example app for development purposes'
    version = '0.0.4'
    author = 'Mathias Wegner'
    author_email = 'mwegner@isc.upenn.edu'
    required_settings = []
    default_settings = {
        'loud': False
    }

config = SSoTEIPSolidServerConfig

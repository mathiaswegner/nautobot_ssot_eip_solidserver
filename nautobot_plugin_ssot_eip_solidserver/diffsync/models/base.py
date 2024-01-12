"""Diffsync models
"""
from typing import Annotated, Optional

import netaddr  # type: ignore
from django.db.models.base import ModelBase  # type: ignore
from nautobot.extras.models import Status  # type: ignore
from nautobot.ipam.models import IPAddress, Prefix  # type: ignore
from nautobot_ssot.contrib import CustomFieldAnnotation, NautobotModel  # type: ignore


class SSoTStatus(NautobotModel):
    """Status model for solidserver ssot plugin"""

    _model: ModelBase = Status
    _modelname = "status"
    _identifiers = ("name",)
    _attributes = ("description", "color")
    name: str = "Imported From Solidserver"
    description: Optional[str]
    color: Optional[str]


class SSoTIPAddress(NautobotModel):
    """IP address model for solidserver ssot plugin"""

    _model: ModelBase = IPAddress
    _modelname = "ipaddress"
    _identifiers = ("host",)
    _attributes = (
        "dns_name",
        "solidserver_addr_id",
        "prefix_length",
        "description",
        "status",
    )
    dns_name: Optional[str]
    description: Optional[str]
    host: netaddr.IPAddress
    solidserver_addr_id: Annotated[
        str, CustomFieldAnnotation(name="solidserver address id")
    ]
    prefix_length: int
    status: SSoTStatus = SSoTStatus(
        name="Imported From Solidserver",
        color="purple",
        description="This IP was imported from Solidserver",
    )


class SSoTIPPrefix(NautobotModel):
    """IP prefix model for solidserver ssot plugin"""

    _model: ModelBase = Prefix
    _modelname = "prefix"
    _identifiers = ("network", "prefix_length")
    _attributes = (
        "description",
        "solidserver_addr_id",
        "status",
    )

    description: Optional[str]
    network: netaddr.IPNetwork
    solidserver_addr_id: Annotated[
        str, CustomFieldAnnotation(name="solidserver address id")
    ]
    prefix_length: int
    status: SSoTStatus = SSoTStatus(
        name="Imported From Solidserver",
        color="purple",
        description="This IP was imported from Solidserver",
    )

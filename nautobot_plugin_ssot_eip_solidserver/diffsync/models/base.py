"""Diffsync models
"""
from typing import Annotated, Optional

import netaddr  # type: ignore
from django.db.models.base import ModelBase  # type: ignore
from nautobot.ipam.models import IPAddress, Prefix  # type: ignore
from nautobot_ssot.contrib import CustomFieldAnnotation, NautobotModel  # type: ignore


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
        "status__name",
    )
    dns_name: Optional[str]
    description: Optional[str | None]
    host: netaddr.IPAddress
    solidserver_addr_id: Annotated[
        str, CustomFieldAnnotation(name="solidserver address id")
    ] = "not found"
    prefix_length: int
    status__name: str = "Imported From Solidserver"


class SSoTIPPrefix(NautobotModel):
    """IP prefix model for solidserver ssot plugin"""

    _model: ModelBase = Prefix
    _modelname = "prefix"
    _identifiers = ("network", "prefix_length")
    _attributes = (
        "description",
        "solidserver_addr_id",
        "status__name",
    )

    description: Optional[str | None]
    network: netaddr.IPNetwork
    solidserver_addr_id: Annotated[
        str, CustomFieldAnnotation(name="solidserver address id")
    ] = "not found"
    prefix_length: int
    status__name: str = "Imported From Solidserver"

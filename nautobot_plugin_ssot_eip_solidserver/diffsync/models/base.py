"""Diffsync models
"""
from typing import Annotated, Optional

import netaddr  # type: ignore
from nautobot_ssot.contrib import CustomFieldAnnotation, NautobotModel


class IPAddress(NautobotModel):
    """IP address model for solidserver ssot plugin"""

    _modelname = "host"
    _identifiers = ("host",)
    _attributes = (
        "dns_name",
        "solidserver_addr_id",
        "mask_length",
        "description",
        "ip_version",
    )
    dns_name: Optional[str]
    description: Optional[str]
    host: netaddr.IPAddress
    solidserver_addr_id: Annotated[
        str, CustomFieldAnnotation(name="solidserver address id")
    ]
    mask_length: int
    ip_version: int


class IPPrefix(NautobotModel):
    """IP prefix model for solidserver ssot plugin"""

    _modelname = "network"
    _identifiers = ("network", "prefix_length")
    _attributes = ("description", "solidserver_addr_id", "ip_version")

    description: Optional[str]
    network: netaddr.IPNetwork
    solidserver_addr_id: Annotated[
        str, CustomFieldAnnotation(name="solidserver address id")
    ]
    prefix_length: int
    ip_version: int

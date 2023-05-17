"""Diffsync models
"""
from typing import Optional
from diffsync import DiffSyncModel


class IPAddress(DiffSyncModel):
    """IP address model for solidserver ssot plugin"""
    _modelname = "address"
    _identifiers = ("address", )
    _shortname = ("address", )
    _attributes = ("dns_name", "nnn_id", "subnet_size",
                   "description", )
    dns_name: Optional[str]
    description: Optional[str]
    address: str
    nnn_id: Optional[int]
    subnet_size: Optional[int]


class IPPrefix(DiffSyncModel):
    """IP prefix model for solidserver ssot plugin"""
    _modelname = "prefix"
    _identifiers = ("prefix", )
    _shortname = ("prefix", )
    _attributes = ("description", "nnn_id", "subnet_size", )

    description: Optional[str]
    prefix: str
    nnn_id: Optional[int]
    subnet_size: Optional[int]

"""Stub model for loading nautobot data back to solidserver.
"""
from nautobot_ssot_eip_solidserver.diffsync.models.base import IPAddress, \
    IPPrefix


class SolidserverIPAddress(IPAddress):
    """Solidserver implementation of IPAddress for Nautobot SSoT"""

    @classmethod
    def update(cls, attrs):
        """Update solidserver with new attr data"""
        return super().update(attrs)

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create new addr from ids, attrs"""
        return super().create(attrs)

    def delete(self):
        """Delete address"""
        return super().delete()


class SolidserverIPPrefix(IPPrefix):
    """Solidserver implementation of IPAddress for Nautobot SSoT"""

    @classmethod
    def update(cls, attrs):
        """Update solidserver with new attr data"""
        return super().update(attrs)

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create new prefix from ids, attrs"""
        return super().create(attrs)

    def delete(self):
        """Delete prefix"""
        return super().delete()

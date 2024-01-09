"""Stub model for loading nautobot data back to solidserver.
Everything is stubbed, nothing is implemented.
"""
from typing import Any, Mapping

from diffsync import DiffSync
from typing_extensions import Self

from nautobot_plugin_ssot_eip_solidserver.diffsync.models.base import (
    IPAddress,
    IPPrefix,
)


class SolidserverIPAddress(IPAddress):
    """Solidserver implementation of IPAddress for Nautobot SSoT"""

    def update(self, attrs: Mapping[Any, Any]) -> Self | None:
        """Update solidserver with new attr data"""
        return super().update(attrs=attrs)

    @classmethod
    def create(
        cls, diffsync: DiffSync, ids: Mapping[Any, Any], attrs: Mapping[Any, Any]
    ) -> Self | None:
        """Create new addr from ids, attrs"""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def delete(self) -> Self | None:
        """Delete address"""
        return super().delete()


class SolidserverIPPrefix(IPPrefix):
    """Solidserver implementation of IPAddress for Nautobot SSoT"""

    def update(self, attrs: Mapping[Any, Any]) -> Self | None:
        """Update solidserver with new attr data"""
        return super().update(attrs)

    @classmethod
    def create(
        cls, diffsync: DiffSync, ids: Mapping[Any, Any], attrs: Mapping[Any, Any]
    ) -> Self | None:
        """Create new prefix from ids, attrs"""
        return super().create(diffsync=diffsync, ids=ids, attrs=attrs)

    def delete(self) -> Self | None:
        """Delete prefix"""
        return super().delete()

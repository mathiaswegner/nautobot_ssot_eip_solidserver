"""CRUD Nautobot objects from DiffSync models via ORM
"""
from typing import Any, Mapping, Union

from diffsync.exceptions import ObjectNotCreated
from django.core.exceptions import ObjectDoesNotExist, ValidationError  # type: ignore
from nautobot.extras.jobs import Job  # type: ignore
from nautobot.extras.models import Status as OrmStatus  # type: ignore
from nautobot.ipam.models import IPAddress as OrmIPAddress  # type: ignore
from nautobot.ipam.models import Prefix as OrmPrefix
from nautobot_ssot.jobs.base import DataSource  # type: ignore
from typing_extensions import Self

from nautobot_plugin_ssot_eip_solidserver.diffsync.models.base import (
    SSoTIPAddress as IPAddress,
)
from nautobot_plugin_ssot_eip_solidserver.diffsync.models.base import (
    SSoTIPPrefix as IPPrefix,
)

SsotDiffSync = Union[Job, DataSource]


class NautobotIPAddress(IPAddress):
    """Nautobot implementation of IPAddress for Nautobot SSoT"""

    @classmethod
    def create(
        cls, diffsync: SsotDiffSync, ids: Mapping[Any, Any], attrs: Mapping[Any, Any]
    ) -> Self | None:
        """Create a nautobot IP address from this model"""
        diffsync.job.log_info(f"Creating address {ids['host']}")
        try:
            obj = OrmIPAddress.objects.get(host=ids["host"])
            diffsync.job.log_warning(f"Tried to create address, but found {obj}")
            return None
        except ObjectDoesNotExist:
            pass
        status = OrmStatus.objects.get(name="Imported From Solidserver")
        if not status:
            diffsync.job.log_warning("Failed to get status 'Imported From Solidserver'")
            return None
        new_address = OrmIPAddress(
            host=ids["host"],
            prefix_length=attrs["prefix_length"],
            dns_name=attrs["dns_name"],
            description=attrs.get("description", ""),
            status=status,
        )
        new_address._custom_field_data = {
            "solidserver_addr_id": str(attrs.get("nnn_id", -1))
        }
        try:
            new_address.validated_save()
        except (ValidationError, ObjectNotCreated) as valid_err:
            # pylance: reportGeneralTypeIssues = false
            diffsync.job.log_warning(f"Failed to create {ids['address']}, {valid_err}")
            return None
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs: Mapping[Any, Any]) -> Self | None:
        """Update a nautobot IP address from this model"""
        self.diffsync.job.log_info(f"Updating address {self.host}")
        if len(attrs) == 1 and "status" in attrs.keys():
            return None
        self.diffsync.job.log_debug("In update, about to get addr object")
        try:
            _address = OrmIPAddress.objects.get(host=str(self.host))
        except (AttributeError, ObjectDoesNotExist) as err:
            message = f"Failed to retrieve {self.host}, {err}"
            self.diffsync.job.log_warning(message)
            return None
        if attrs.get("dns_name"):
            _address.dns_name = attrs["dns_name"]
        if attrs.get("prefix_length"):
            _address.prefix_length = int(attrs.get("prefix_length"))
        if attrs.get("description"):
            _address.description = attrs["description"]
        if attrs.get("solidserver_addr_id"):
            self.diffsync.job.log_debug(
                f"Setting solidserver_addr_id to {attrs.get('solidserver_addr_id')} as"
                " update in place"
            )
            _address._custom_field_data["solidserver_addr_id"] = str(
                attrs.get("solidserver_addr_id", "-1")
            )
        elif attrs.get("dns_name") == "":
            self.diffsync.job.log_debug(
                "Setting solidserver_addr_id to -1 after dns_name == ''"
            )
            try:
                _address._custom_field_data["solidserver_addr_id"] = "-1"
            except (AttributeError, KeyError):
                self.diffsync.job.log_debug(
                    "Setting solidserver_addr_id to -1 after exception dns_name = ''"
                )
                _address._custom_field_data = {"solidserver_addr_id": "-1"}
            status = OrmStatus.objects.get(name="NO-IPAM-RECORD")
            if not status:
                self.diffsync.job.log_warning("Failed to get status 'NO-IPAM-RECORD'")
                return None
            self.diffsync.job.log_debug(f"Got status {status}")
            _address.status = status
        else:
            status = OrmStatus.objects.get(name="Unknown")
            if not status:
                self.diffsync.job.log_warning("Failed to get status 'Unknown'")
                return None
            self.diffsync.job.log_debug(f"Got status {status}")
            _address.status = status
        try:
            _address.validated_save()
        except (ValidationError, ObjectNotCreated) as update_err:
            message = f"Failed to save update to {_address.host}: {update_err}"
            self.diffsync.job.log_warning(message)
            return None
        return super().update(attrs)

    def delete(self) -> Self:
        """Delete a nautobot IP address that matches this model"""
        self.diffsync.job.log_warning(f"Address {self.host} will be deleted.")
        try:
            self.diffsync.job.log_debug(
                f"Trying host={self.get_identifiers().get('address')}"
            )
            address = OrmIPAddress.objects.get(
                host=self.get_identifiers().get("address")
            )
            address.delete()
            super().delete()
            self.diffsync.job.log_debug("SUCCESS!")
        except ObjectDoesNotExist:
            self.diffsync.job.log_warning(
                f"Failed to delete {self.host}, got DoesNotExist error!"
            )
            self.diffsync.job.log_debug(
                f"host={self.get_identifiers().get('host')} FAILED"
            )
        return self


class NautobotIPPrefix(IPPrefix):
    """Nautobot implementation of IPPrefix for Nautobot SSoT"""

    @classmethod
    def create(
        cls, diffsync: SsotDiffSync, ids: Mapping[Any, Any], attrs: Mapping[Any, Any]
    ) -> Self | None:
        """Create a nautobot IP prefix from this model"""
        diffsync.job.log_info(
            f"Creating prefix {ids['network']}/{ids['prefix_length']}"
        )
        try:
            obj = OrmPrefix.objects.get(
                prefix=ids["network"], prefix_length=ids["prefix_length"]
            )
            diffsync.job.log_warning(f"Tried to create prefix, but found {obj}")
            return None
        except ObjectDoesNotExist:
            pass
        status = OrmStatus.objects.get(name="Imported From Solidserver")
        if not status:
            diffsync.job.log_warning("Failed to get status 'Imported From Solidserver'")
            return None
        if ids["prefix_length"] == 128:
            diffsync.job.log_warning(f"prefix {ids['network']} has /128 mask")
        elif ids["prefix_length"] == 129:
            diffsync.job.log_warning(
                f"prefix {ids['network']} failed to get subnet6_prefix"
            )
            return None
        new_prefix = OrmPrefix(
            network=ids["network"],
            prefix_length=ids["prefix_length"],
            description=attrs.get("description", ""),
            status=status,
        )
        new_prefix._custom_field_data = {
            "solidserver_addr_id": str(attrs.get("solidserver_addr_id", "-1"))
        }
        try:
            new_prefix.validated_save()
        except (ValidationError, ObjectNotCreated) as create_err:
            diffsync.job.log_warning(
                f"Failed to create {ids['network']}/{ids['prefix_length']}, "
                + f"{create_err}"
            )
            return None
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs: Mapping[Any, Any]) -> Self | None:
        """Update a nautobot IP address from this model"""
        self.diffsync.job.log_info(f"Updating prefix {self.network}")
        try:
            _prefix = OrmPrefix.objects.get(
                network=self.network, prefix_length=self.prefix_length
            )
        except (AttributeError, ObjectDoesNotExist) as err:
            message = f"Failed to update prefix with attrs {attrs}, {err}"
            self.diffsync.job.log_warning(message)
            return None
        if attrs.get("description"):
            _prefix.description = attrs["description"]
        if attrs.get("solidserver_addr_id"):
            try:
                _prefix._custom_field_data["solidserver_addr_id"] = str(
                    attrs.get("solidserver_addr_id", "-1")
                )
            except (AttributeError, KeyError):
                _prefix._custom_field_data = {
                    "solidserver_addr_id": str(attrs.get("solidserver_addr_id", "-1"))
                }
        elif attrs.get("description") == "":
            try:
                _prefix._custom_field_data["solidserver_addr_id"] = "-1"
            except (AttributeError, KeyError):
                _prefix._custom_field_data = {
                    "solidserver_addr_id": str(attrs.get("solidserver_addr_id", "-1"))
                }
            status = OrmStatus.objects.get(name="NO-IPAM-RECORD")
            if not status:
                self.diffsync.job.log_warning("Failed to get status 'NO-IPAM-RECORD'")
                return None
            self.diffsync.job.log_debug(f"Got status {status}")
            _prefix.status = status
        else:
            status = OrmStatus.objects.get(name="Unknown")
            if not status:
                self.diffsync.job.log_warning("Failed to get status 'Unknown'")
                return None
            self.diffsync.job.log_debug(f"Got status {status}")
            _prefix.status = status
        try:
            _prefix.validated_save()
        except (ValidationError, ObjectNotCreated) as update_err:
            self.diffsync.job.log_warning(
                f"Failed to update prefix {self.network}/{self.prefix_length}, "
                + f"{update_err}"
            )
            return None
        return super().update(attrs)

    def delete(self) -> Self:
        """Delete a nautobot IP address that matches this model"""
        self.diffsync.job.log_warning(f"Prefix {self.network} will be deleted.")
        try:
            self.diffsync.job.log_debug(
                f"Trying prefix={self.get_identifiers().get('prefix')}"
            )
            prefix = OrmPrefix.objects.get(prefix=self.get_identifiers().get("prefix"))
            prefix.delete()
            super().delete()
        except ObjectDoesNotExist:
            self.diffsync.job.log_warning(
                f"Failed to delete {self.network}, got DoesNotExist error!"
            )
            self.diffsync.job.log_debug(
                f"prefix={self.get_identifiers().get('prefix')} FAILED"
            )
        return self

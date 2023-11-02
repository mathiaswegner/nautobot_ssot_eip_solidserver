"""CRUD Nautobot objects from DiffSync models via ORM
"""
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from nautobot.extras.models import Status as OrmStatus
from nautobot.ipam.models import IPAddress as OrmIPAddress
from nautobot.ipam.models import Prefix as OrmPrefix
from nautobot_ssot_eip_solidserver.diffsync.models.base import (IPAddress,
                                                                IPPrefix)

from diffsync.exceptions import ObjectNotCreated


class NautobotIPAddress(IPAddress):
    """Nautobot implementation of IPAddress for Nautobot SSoT"""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create a nautobot IP address from this model"""
        status = OrmStatus.objects.get(name__isw="active")
        new_address = OrmIPAddress(
            host=ids["address"], prefix_length=attrs["subnet_size"],
            dns_name=attrs["dns_name"],
            description=attrs.get("notes", ""),
            status=status
        )
        new_address._custom_field_data = {
            "solidserver_addr_id": str(attrs.get("nnn_id", -1))}
        try:
            new_address.validated_save()
        except (ValidationError, ObjectNotCreated) as valid_err:
            diffsync.job.log_warning(
                f"Failed to create {ids['address']}, {valid_err}")
            return None
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update a nautobot IP address from this model"""
        self.diffsync.job.log_info(f"Updating address {self.address}")
        if len(attrs) == 1 and 'status' in attrs.keys():
            return
        if '/' in self.address:
            host_addr = str(self.address).split('/', maxsplit=1)[0]
        else:
            host_addr = str(self.address)
        self.diffsync.job.log_debug("In update, about to get addr object")
        try:
            _address = OrmIPAddress.objects.get(host=host_addr)
        except (AttributeError, OrmIPAddress.DoesNotExist) as err:
            message = f"Failed to retrieve {host_addr}, {err}"
            self.diffsync.job.log_warning(message)
            return
        if attrs.get("dns_name"):
            _address.dns_name = attrs["dns_name"]
        if attrs.get("subnet_size"):
            if isinstance(attrs.get("subnet_size"), str) and \
                    '/' in attrs.get("subnet_size"):
                _address.prefix_length = str(
                    attrs.get("subnet_size")).split('/')[1]
            else:
                _address.prefix_length = attrs.get("subnet_size")
        if attrs.get("description"):
            _address.description = attrs["description"]
        if attrs.get("nnn_id"):
            self.diffsync.job.log_debug(
                f"Setting nnn_id to {attrs.get('nnn_id')} as update in place")
            _address._custom_field_data["solidserver_addr_id"] = \
                str(attrs.get("nnn_id", "-1"))
        elif attrs.get("dns_name") == "":
            self.diffsync.job.log_debug(
                "Setting nnn_id to -1 after dns_name == ''"
            )
            try:
                _address._custom_field_data["solidserver_addr_id"] = "-1"
            except (AttributeError, KeyError):
                self.diffsync.job.log_debug(
                    "Setting nnn_id to -1 after exception dns_name = ''"
                )
                _address._custom_field_data = {"solidserver_addr_id": "-1"}
            no_record = OrmStatus.objects.get(name="NO-IPAM-RECORD")
            self.diffsync.job.log_debug("Got status %s", no_record)
            _address.status = no_record
        else:
            unknown = OrmStatus.objects.get(name__isw="Unknown")
            self.diffsync.job.log_debug("Got status %s", unknown)
            _address.status = unknown
        try:
            _address.validated_save()
        except (ValidationError, ObjectNotCreated) as update_err:
            message = f"Failed to save update to {host_addr}: {update_err}"
            self.diffsync.job.log_warning(message)
            return
        return super().update(attrs)

    def delete(self):
        """Delete a nautobot IP address that matches this model"""
        self.diffsync.job.log_warning(
            f"Address {self.address} will be deleted.")
        try:
            self.diffsync.job.log_debug(
                f"Trying host={self.get_identifiers().get('address')}"
            )
            address = OrmIPAddress.objects.get(
                host=self.get_identifiers().get('address'))
            address.delete()
            super().delete()
            self.diffsync.job.log_debug('SUCCESS!')
        except (OrmIPAddress.DoesNotExist, ObjectDoesNotExist):
            self.diffsync.job.log_warning(
                f"Failed to delete {self.address}, got DoesNotExist error!"
            )
            self.diffsync.job.log_debug(
                f"host={self.get_identifiers().get('address')} FAILED"
            )
        return self


class NautobotIPPrefix(IPPrefix):
    """Nautobot implementation of IPPrefix for Nautobot SSoT"""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create a nautobot IP prefix from this model"""
        # cls.diffsync.job.log_info(f"Creating prefix {ids['prefix']}")
        # if attrs["status"]:
        #     status = OrmStatus.objects.get(name=attrs["status"])
        # else:
        diffsync.job.log_info(
            f"Creating prefix {ids['prefix']}/{ids['subnet_size']}")
        try:
            obj = OrmPrefix.objects.get(prefix=ids["prefix"],
                                        prefix_length=ids["subnet_size"])
            diffsync.job.log_warning(
                f"Tried to create prefix, but found {obj}")
            return None
        except ObjectDoesNotExist:
            pass
        status = OrmStatus.objects.get(name__isw="Active")
        if ids['subnet_size'] == 128:
            diffsync.job.log_warning(f"prefix {ids['prefix']} has /128 mask")
        elif ids['subnet_size'] == 129:
            diffsync.job.log_warning(
                f"prefix {ids['prefix']} failed to get subnet6_prefix")
            return None
        new_prefix = OrmPrefix(
            network=ids['prefix'],
            prefix_length=ids['subnet_size'],
            description=attrs.get("description", ""),
            status=status
        )
        new_prefix._custom_field_data = {
            "solidserver_addr_id": str(attrs.get("nnn_id", "-1"))}
        try:
            new_prefix.validated_save()
        except (ValidationError, ObjectNotCreated) as create_err:
            diffsync.job.log_warning(
                f"Failed to create {ids['prefix']}/{ids['subnet_size']}, "
                + f"{create_err}")
            return None
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update a nautobot IP address from this model"""
        self.diffsync.job.log_info(f"Updating prefix {self.prefix}")
        try:
            _prefix = OrmPrefix.objects.get(network=self.prefix,
                                            prefix_length=self.subnet_size)
        except (AttributeError, OrmPrefix.DoesNotExist) as err:
            message = f"Failed to update prefix with attrs {attrs}, {err}"
            self.diffsync.job.log_warning(message)
            return None
        if attrs.get("description"):
            _prefix.description = attrs["description"]
        if attrs.get("nnn_id"):
            try:
                _prefix._custom_field_data["solidserver_addr_id"] = \
                    str(attrs.get("nnn_id", "-1"))
            except (AttributeError, KeyError):
                _prefix._custom_field_data = {
                    "solidserver_addr_id": str(attrs.get("nnn_id", "-1"))}
        elif attrs.get("description") == "":
            try:
                _prefix._custom_field_data["solidserver_addr_id"] = "-1"
            except (AttributeError, KeyError):
                _prefix._custom_field_data = {
                    "solidserver_addr_id": str(attrs.get("nnn_id", "-1"))}
            no_record = OrmStatus.objects.get(name="NO-IPAM-RECORD")
            self.diffsync.job.log_debug("Got status %s", no_record)
            _prefix.status = no_record
        else:
            unknown = OrmStatus.objects.get(name__isw="Unknown")
            self.diffsync.job.log_debug("Got status %s", unknown)
            _prefix.status = unknown
        try:
            _prefix.validated_save()
        except (ValidationError, ObjectNotCreated) as update_err:
            self.diffsync.job.log_warning(
                f"Failed to update prefix {self.prefix}/{self.subnet_size}, "
                + f"{update_err}")
            return None
        return super().update(attrs)

    def delete(self):
        """Delete a nautobot IP address that matches this model"""
        self.diffsync.job.log_warning(
            f"Prefix {self.prefix} will be deleted.")
        try:
            self.diffsync.job.log_debug(
                f"Trying prefix={self.get_identifiers().get('prefix')}"
            )
            prefix = OrmPrefix.objects.get(
                prefix=self.get_identifiers().get('prefix')
            )
            prefix.delete()
            super().delete()
        except (OrmPrefix.DoesNotExist, ObjectDoesNotExist):
            self.diffsync.job.log_warning(
                f"Failed to delete {self.prefix}, got DoesNotExist error!"
            )
            self.diffsync.job.log_debug(
                f"prefix={self.get_identifiers().get('prefix')} FAILED"
            )
        return self

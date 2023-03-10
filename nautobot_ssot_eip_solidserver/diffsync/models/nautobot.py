from nautobot.extras.models import Status as OrmStatus
import nautobot.extras.models.statuses
from nautobot.ipam.models import IPAddress as OrmIPAddress
from nautobot.ipam.models import Prefix as OrmPrefix
from nautobot_ssot_eip_solidserver.diffsync.models.base import IPAddress, \
     IPPrefix


class NautobotIPAddress(IPAddress):
    """Nautobot implementation of IPAddress for Nautobot SSoT"""

    @classmethod
    def create(cls, diffsync, ids, attrs):
        """Create a nautobot IP address from this model"""
        # self.diffsync.job.log_info(f"Creating address {ids['address']}")
        # if attrs["status"]:
        #     try:
        #         status = OrmStatus.objects.get(name=attrs["status"])
        #     except nautobot.extras.models.statuses.Status.DoesNotExist:
        #         status = OrmStatus.objects.get(name="Unknown")
        # else:
        status = OrmStatus.objects.get(name="Imported From Solidserver")
        new_address = OrmIPAddress(
            host=ids["address"], prefix_length=attrs["subnet_size"],
            dns_name=attrs["dns_name"],
            description=attrs.get("notes", ""),
            status=status
        )
        new_address._custom_field_data = {
            "solidserver_addr_id": attrs.get("nnn_id", "")}
        new_address.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update a nautobot IP address from this model"""
        self.diffsync.job.log_info(f"Updating address {self.address}")
        if len(attrs) == 1 and 'status' in attrs.keys():
            return
        if '/' in self.address:
            host_addr = str(self.address).split('/')[0]
        else:
            host_addr = str(self.address)
        self.diffsync.job.log_debug(f"In update, about to get addr object")
        try:
            _address = OrmIPAddress.objects.get(host=host_addr)
        except (AttributeError, OrmIPAddress.DoesNotExist) as err:
            message = f"Failed to update with attrs {attrs}, {err}"
            self.diffsync.job.log_warning(message)
            return
        if attrs.get("dns_name"):
            _address.dns_name = attrs["dns_name"]
        if attrs.get("subnet_size"):
            if '/' in attrs.get("subnet_size"):
                _address.prefix_length = str(
                    attrs.get("subnet_size")).split('/')[1]
            else:
                _address.prefix_length = attrs.get("subnet_size")
        if attrs.get("description"):
            _address.description = attrs["description"]
        if attrs.get("nnn_id"):
            _address._custom_field_data["solidserver_addr_id"] = \
                attrs.get("nnn_id")
            # if attrs.get("status"):
            #     try:
            #         _address.status = OrmStatus.objects.get(
            #             name=attrs["status"])
            #     except nautobot.extras.models.statuses.Status.DoesNotExist:
            #         _address.status = OrmStatus.objects.get(name="Unknown")
        elif attrs.get("dns_name") == "":
            try:
                _address._custom_field_data["solidserver_addr_id"] = ""
            except (AttributeError, KeyError):
                _address._custom_field_data = {"solidserver_addr_id": ""}
            _address.status = OrmStatus.objects.get(name="NO-IPAM-RECORD")
        else:
            # if attrs.get("status"):
            #     try:
            #         _address.status = OrmStatus.objects.get(
            #             name=attrs["status"])
            #     except nautobot.extras.models.statuses.Status.DoesNotExist:
            _address.status = OrmStatus.objects.get(name="Unknown")
        try:
            _address.validated_save()
        except Exception as catchall:
            message = f"Failed to update {host_addr}: {catchall}"
            self.diffsync.job.log_warning(message)
            return
        return super().update(attrs)

    def delete(self):
        """Delete a nautobot IP address that matches this model"""
        self.diffsync.job.log_warning(
            f"Address {self.address} will be deleted.")
        address = OrmIPAddress.objects.get(**self.get_identifiers())
        address.delete()
        super().delete()
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
        status = OrmStatus.objects.get(name="Imported From Solidserver")
        new_prefix = OrmPrefix(
            prefix=ids['prefix'], prefix_length=attrs['subnet_size'],
            description=attrs.get("description", ""),
            status=status
        )
        new_prefix._custom_field_data = {
            "solidserver_addr_id": attrs.get("nnn_id", "")}
        new_prefix.validated_save()
        return super().create(ids=ids, diffsync=diffsync, attrs=attrs)

    def update(self, attrs):
        """Update a nautobot IP address from this model"""
        cls.diffsync.job.log_info(f"Updating prefix {self.prefix}")
        try:
            _prefix = OrmPrefix.objects.get(network=self.prefix)
        except (AttributeError, OrmPrefix.DoesNotExist) as err:
            message = f"Failed to update prefix with attrs {attrs}, {err}"
            self.diffsync.job.log_warning(message)
            return
        if attrs.get("description"):
            _prefix.description = attrs["description"]
        if attrs.get("subnet_size"):
            _prefix.prefix_length = attrs["subnet_size"]
        if attrs.get("nnn_id"):
            try:
                _prefix._custom_field_data["solidserver_addr_id"] = \
                    attrs.get("nnn_id")
            except (AttributeError, KeyError):
                _prefix._custom_field_data = {
                    "solidserver_addr_id": attrs.get("nnn_id", "")}
            # try:
            #     _prefix.status = OrmStatus.objects.get(name=attrs["status"])
            # except nautobot.extras.models.statuses.Status.DoesNotExist:
            #     _prefix.status = OrmStatus.objects.get(name="Unknown")
        elif attrs.get("description") == "":
            try:
                _prefix._custom_field_data["solidserver_addr_id"] = ""
            except (AttributeError, KeyError):
                _prefix._custom_field_data = {
                    "solidserver_addr_id": attrs.get("nnn_id", "")}
            _prefix.status = OrmStatus.objects.get(name="NO-IPAM-RECORD")
        else:
            # if attrs.get("status"):
            #     try:
            #         _prefix.status = OrmStatus.objects.get(
            #             name=attrs["status"])
            #     except nautobot.extras.models.statuses.Status.DoesNotExist:
            _prefix.status = OrmStatus.objects.get(name="Unknown")
        try:
            _prefix.validated_save()
        except Exception as catchall:
            message = f"Failed to update {self.prefix}: {catchall}"
            self.diffsync.job.log_warning(message)
            return
        return super().update(attrs)

    def delete(self):
        """Delete a nautobot IP address that matches this model"""
        self.diffsync.job.log_warning(
            f"Prefix {self.prefix} will be deleted.")
        super().delete()
        prefix = OrmPrefix.objects.get(**self.get_identifiers())
        prefix.delete()
        return self

from nautobot_ssot_eip_solidserver.diffsync.models.base import IPAddress, \
    IPPrefix


class SolidserverIPAddress(IPAddress):
    """Solidserver implementation of IPAddress for Nautobot SSoT"""

    @classmethod
    def update(cls, attrs):
        """Update solidserver with new attr data"""
        # json = {"configure_for_dns": False}
        # if attrs.get("description"):
        #     json.update({"comment": attrs["description"]})
        # if attrs.get("dns_name"):
        #     json.update({"name": attrs["dns_name"]})
        # if json:
        #     self.diffsync.conn.update_ipaddress(
        # ip_address=self.get_identifiers()["address"], data=json)
        return super().update(attrs)

    @classmethod
    def create(cls, diffsync, ids, attrs):
        return super().create(attrs)

    def delete(self):
        return super().delete()


class SolidserverIPPrefix(IPPrefix):
    """Solidserver implementation of IPAddress for Nautobot SSoT"""

    @classmethod
    def update(cls, attrs):
        """Update solidserver with new attr data"""
        # json = {"configure_for_dns": False}
        # if attrs.get("description"):
        #     json.update({"comment": attrs["description"]})
        # if attrs.get("dns_name"):
        #     json.update({"name": attrs["dns_name"]})
        # if json:
        #     self.diffsync.conn.update_ipaddress(
        # ip_address=self.get_identifiers()["address"], data=json)
        return super().update(attrs)

    @classmethod
    def create(cls, diffsync, ids, attrs):
        return super().create(attrs)

    def delete(self):
        return super().delete()

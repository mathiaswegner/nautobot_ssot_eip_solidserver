"""Adapt Nautobot ORM objects into diffsync models
"""
import netaddr  # type: ignore
from diffsync.exceptions import ObjectAlreadyExists
from nautobot.extras.jobs import Job  # type: ignore
from nautobot.ipam.models import IPAddress  # type: ignore
from nautobot.ipam.models import Prefix
from nautobot_ssot.contrib import NautobotAdapter  # type: ignore
from nautobot_ssot.models import Sync  # type: ignore
from netaddr import AddrFormatError

from nautobot_plugin_ssot_eip_solidserver.diffsync.models.base import (
    SSoTIPAddress,
    SSoTIPPrefix,
)


class SSoTNautobotAdapter(NautobotAdapter):
    """DiffSync adapter for Nautobot server."""

    ipaddress = SSoTIPAddress
    prefix = SSoTIPPrefix

    top_level = ["ipaddress", "prefix"]

    def __init__(self, *args, job: Job, sync: Sync, **kwargs):
        """Initialize the Nautobot DiffSync adapter."""
        super().__init__(*args, **kwargs)
        self.job: Job = job
        self.sync: Sync = sync

    def _load_one_ipaddress(self, ipaddr: IPAddress) -> None:
        """Create a single IPAddress object and load it into the adapter model.

        Args:
            ipaddr (IPAddress): The IPAddress object to load.
        """
        self.job.log_debug(f"Adapter loading address {ipaddr.host}")
        try:
            addr_id: str = ipaddr._custom_field_data.get("solidserver_addr_id")
        except (AttributeError, TypeError, ValueError):
            addr_id = "not found"
        new_ip = self.ipaddress(
            host=netaddr.IPAddress(ipaddr.host),
            dns_name=ipaddr.dns_name,
            description=ipaddr.description,
            solidserver_addr_id=addr_id,
            prefix_length=ipaddr.prefix_length,
        )
        message = f"Loaded address {ipaddr.host}"
        self.job.log_debug(message=message)
        try:
            self.add(new_ip)
        except ObjectAlreadyExists as err:
            self.job.log_warning(f"Unable to load duplicate {ipaddr.address}. {err}")

    def _load_one_prefix(self, prefix: Prefix) -> None:
        """Create a single Prefix object and load it into the adapter model.

        Args:
            prefix (Prefix): The Prefix object to load.
        """
        self.job.log_debug(f"Adapter loading prefix {prefix.prefix}")
        if not prefix._custom_field_data.get("solidserver_addr_id"):
            self.job.log_warning(
                f"Prefix {prefix.prefix} has no solidserver_addr_id," + " skipping!"
            )
            return None
        try:
            addr_id: str = prefix._custom_field_data.get("solidserver_addr_id")
        except (AttributeError, TypeError):
            addr_id = "not found"
        new_prefix = self.prefix(
            network=netaddr.IPNetwork(f"{prefix.network}/{prefix.prefix_length}"),
            prefix_length=prefix.prefix_length,
            description=prefix.description,
            solidserver_addr_id=addr_id,
        )
        try:
            self.add(new_prefix)
        except ObjectAlreadyExists as err:
            self.job.log_warning(
                f"Unable to load duplicate {new_prefix.network}. {err}"
            )

    def _load_filtered_ip_addresses(self, filter_field, this_filter):
        """Collect ip addresses from ORM, create models, load into diffsync

        Args:
            filter_field (str): type of filter
            this_filter (str or list): the filter data for this IP load
        """
        filtered_addrs = []
        if filter_field == "host__net_in":
            if not isinstance(this_filter, list):
                this_filter = [this_filter]
            message = f"host__net_in={this_filter}"
            self.job.log_debug(message=message)
            filtered_addrs = IPAddress.objects.filter(host__net_in=this_filter)
        elif filter_field == "dns_name__icontains":
            message = f"dns_name__icontains={this_filter}"
            self.job.log_debug(message=message)
            filtered_addrs = IPAddress.objects.filter(dns_name__icontains=this_filter)
        for ipaddr in filtered_addrs:
            self._load_one_ipaddress(ipaddr)

    def _load_filtered_ip_prefixes(self, filter_field, this_filter):
        """Collect ip prefixes from ORM, create models, load into diffsync

        Args:
            filter_field (str): filter type
            this_filter (str): the filter to use
        """
        filtered_prefixes = []
        self.job.log_debug(f"Getting prefixes in {this_filter}")
        if filter_field == "prefix__net_contained_or_equal":
            filtered_prefixes = Prefix.objects.filter(
                network__net_contained_or_equal=this_filter
            )
        elif filter_field == "prefix":
            filtered_prefixes = Prefix.objects.filter(network=this_filter)
        self.job.log_debug(f"Processing {len(filtered_prefixes)} prefixes")
        for prefix in filtered_prefixes:
            self._load_one_prefix(prefix)

    def load_ip_addresses(self, address_filter=None, domain_filter=None):
        """Add Nautobot IPAddress objects as DiffSync IPAddress models."""
        if address_filter:
            try:
                this_cidr = netaddr.IPNetwork(address_filter)
            except (ValueError, AddrFormatError) as valerr:
                raise ValueError("Invalid network CIDR") from valerr
            this_filter = f"{str(this_cidr)}"  # parent
            self._load_filtered_ip_addresses(
                filter_field="host__net_in", this_filter=[this_filter]
            )
        if domain_filter:
            if not isinstance(domain_filter, list):
                domain_filter = domain_filter.split(",")
            message = f"Starting domain_filter with {domain_filter}"
            self.job.log_debug(message=message)
            for each_domain in domain_filter:
                message = f"each_domain is {each_domain}"
                self.job.log_debug(message=message)
                this_filter = f"{each_domain.strip().lstrip()}"
                # dns_name__icontains
                self._load_filtered_ip_addresses(
                    filter_field="dns_name__icontains", this_filter=this_filter
                )
        if not address_filter and not domain_filter:
            for ipaddr in IPAddress.objects.all():
                self._load_one_ipaddress(ipaddr)

    def load_ip_prefixes(self, address_filter):
        """Add Nautobot IPPrefix objects as DiffSync IPPrefix models."""
        # TO-DO add filters for domain name
        if address_filter:
            try:
                this_cidr = netaddr.IPNetwork(address_filter)
            except (ValueError, AddrFormatError) as valerr:
                raise ValueError("Invalid network CIDR") from valerr
            this_filter = f"{str(this_cidr)}"  # prefix__net_contains
            self._load_filtered_ip_prefixes(
                filter_field="prefix__net_contained_or_equal", this_filter=this_filter
            )
        if not address_filter:
            # for now, getting all prefixes when domain filter is present
            # there's not a good way to map domain name to prefix.
            self.job.log_debug(f"Processing {len(Prefix.objects.all())} prefixes")
            for prefix in Prefix.objects.all():
                self._load_one_prefix(prefix)

    def load(self, addrs=True, prefixes=True, address_filter=None, domain_filter=None):
        """jobs facing method, coordinates which private methods to run and
        handle arguments

        Args:
            addrs (bool, optional): Load addresses? Defaults to True.
            prefixes (bool, optional): Load prefixes? Defaults to True.
            address_filter (netaddr.IPNetwork, optional): Filter to use
            with addresses/prefixes.
              Defaults to None.
            domain_filter (str, optional): Filter to use with prefixes.
              Defaults to None.
        """
        if addrs:
            self.job.log_info(message="Starting to load IP addresses")
            self.load_ip_addresses(address_filter, domain_filter)
        if prefixes:
            self.job.log_info(message="Starting to load prefixes")
            self.load_ip_prefixes(address_filter)

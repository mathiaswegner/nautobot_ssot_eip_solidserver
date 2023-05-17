"""Adapt Nautobot ORM objects into diffsync models
"""
import netaddr
from nautobot.ipam.models import IPAddress as OrmIPAddress
from nautobot.ipam.models import Prefix as OrmIPPrefix
from nautobot_ssot_eip_solidserver.diffsync.models.nautobot import \
    NautobotIPAddress, NautobotIPPrefix
from diffsync import DiffSync
from diffsync.exceptions import ObjectAlreadyExists


class NautobotAdapter(DiffSync):
    """DiffSync adapter for Nautobot server."""

    address = NautobotIPAddress
    prefix = NautobotIPPrefix

    top_level = ["address"]

    def __init__(self, *args, job=None, sync=None, **kwargs):
        """Initialize the Nautobot DiffSync adapter."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.sync = sync

    def _load_filtered_ip_addresses(self, filter_field, this_filter):
        """Collect ip addresses from ORM, create models, load into diffsync

        Args:
            filter_field (str): type of filter
            this_filter (str or list): the filter data for this IP load
        """
        if filter_field == 'host__net_in':
            if not isinstance(this_filter, list):
                this_filter = [this_filter]
            message = f"host__net_in={this_filter}"
            self.job.log_debug(message=message)
            filtered_addrs = OrmIPAddress.objects.filter(
                host__net_in=this_filter)
        elif filter_field == 'dns_name__icontains':
            message = f"dns_name__icontains={this_filter}"
            self.job.log_debug(message=message)
            filtered_addrs = OrmIPAddress.objects.filter(
                dns_name__icontains=this_filter)
        for ipaddr in filtered_addrs:
            try:
                addr_id = int(ipaddr._custom_field_data.get(
                    'solidserver_addr_id'))
            except (AttributeError, TypeError, ValueError):
                addr_id = -1
            subnet_size = None
            if '/' in str(ipaddr.address):
                split_addr = str(ipaddr.address).split('/')
                this_addr = split_addr[0]
                subnet_size = split_addr[1]
            else:
                this_addr = str(ipaddr.address)
            new_ip = self.address(
                address=this_addr,
                dns_name=ipaddr.dns_name,
                description=ipaddr.description,
                nnn_id=addr_id,
                subnet_size=subnet_size
            )
            message = f"Loaded address {this_addr}"
            self.job.log_debug(message=message)
            try:
                self.add(new_ip)
            except ObjectAlreadyExists as err:
                self.job.log_warning(
                    f"Unable to load duplicate {ipaddr.address}. {err}")

    def _load_filtered_ip_prefixes(self, filter_field, this_filter):
        """Collect ip prefixes from ORM, create models, load into diffsync

        Args:
            filter_field (str): filter type
            this_filter (str): the filter to use
        """
        if filter_field == 'prefix__net_contains':
            filtered_prefixes = OrmIPPrefix.objects.filter(
                network__net_contains=this_filter)
        elif filter_field == 'prefix':
            filtered_prefixes = OrmIPPrefix.objects.filter(
                network=this_filter)
        for prefix in filtered_prefixes:
            try:
                addr_id = int(prefix.custom_fields.solidserver_addr_id)
            except (AttributeError, TypeError):
                addr_id = None
            new_prefix = self.prefix(
                prefix=str(prefix.network),
                description=prefix.description,
                # status=prefix.status.name,
                nnn_id=addr_id
            )
            try:
                self.add(new_prefix)
            except ObjectAlreadyExists as err:
                self.job.log_warning(
                    f"Unable to load duplicate {new_prefix.prefix}. {err}")

    def _load_ip_addresses(self, address_filter=None, domain_filter=None):
        """Add Nautobot IPAddress objects as DiffSync IPAddress models."""
        if address_filter:
            try:
                this_cidr = netaddr.IPNetwork(address_filter)
            except (ValueError, netaddr.core.AddrFormatError) as valerr:
                raise ValueError('Invalid network CIDR') from valerr
            this_filter = f"{str(this_cidr)}"  # parent
            self._load_filtered_ip_addresses(filter_field='host__net_in',
                                             this_filter=[this_filter])
        if domain_filter:
            if not isinstance(domain_filter, list):
                domain_filter = domain_filter.split(',')
            message = f"Starting domain_filter with {domain_filter}"
            self.job.log_debug(message=message)
            for each_domain in domain_filter:
                message = f"each_domain is {each_domain}"
                self.job.log_debug(message=message)
                this_filter = f"{each_domain.strip().lstrip()}"
                # dns_name__icontains
                self._load_filtered_ip_addresses(
                    filter_field='dns_name__icontains',
                    this_filter=this_filter)
        if not address_filter and not domain_filter:
            for ipaddr in OrmIPAddress.objects.all():
                try:
                    addr_id = int(ipaddr._custom_field_data.get(
                        "solidserver_addr_id"))
                except (AttributeError, TypeError):
                    addr_id = None
                subnet_size = None
                if '/' in str(ipaddr.address):
                    split_addr = str(ipaddr.address).split('/')
                    this_addr = split_addr[0]
                    subnet_size = split_addr[1]
                else:
                    this_addr = str(ipaddr.address)
                new_ip = self.address(
                    address=this_addr,
                    dns_name=ipaddr.dns_name,
                    description=ipaddr.description,
                    nnn_id=addr_id,
                    subnet_size=subnet_size
                )
                message = f"Loaded address {this_addr}"
                self.job.log_debug(message=message)
                try:
                    self.add(new_ip)
                except ObjectAlreadyExists as err:
                    self.job.log_warning(
                        f"Unable to load duplicate {ipaddr.address}. {err}")

    def _load_ip_prefixes(self, address_filter):
        """Add Nautobot IPPrefix objects as DiffSync IPPrefix models."""
        # TO-DO add filters for domain name, CIDR
        if address_filter:
            try:
                this_cidr = netaddr.IPNetwork(address_filter)
            except (ValueError, netaddr.core.AddrFormatError) as valerr:
                raise ValueError('Invalid network CIDR') from valerr
            this_filter = f"{str(this_cidr)}"  # prefix__net_contains
            self._load_filtered_ip_prefixes(
                filter_field='prefix__net_contains', this_filter=this_filter)
        # if domain_filter:
        #     for each_net in domain_filter:
        #         this_filter = f"{each_net}"  # prefix
        #         self._load_filtered_ip_prefixes(filter_field='prefix',
        #                                         this_filter=this_filter)
        # if not address_filter and not domain_filter:
        if not address_filter:
            # for now, getting all prefixes when domain filter is present
            # there's not a good way to map domain name to prefix.
            for prefix in OrmIPPrefix.objects.all():
                try:
                    addr_id = int(prefix.custom_fields.solidserver_addr_id)
                except (AttributeError, TypeError):
                    addr_id = None
                new_prefix = self.prefix(
                    prefix=str(prefix.network),
                    description=prefix.description,
                    # status=prefix.status.name,
                    nnn_id=addr_id
                )
                try:
                    self.add(new_prefix)
                except ObjectAlreadyExists as err:
                    self.job.log_warning(
                        f"Unable to load duplicate {new_prefix.prefix}. {err}")

    def load(self, addrs=True, prefixes=True, address_filter=None,
             domain_filter=None):
        """jobs facing method, coordinates which private methods to run and
        handle arguments

        Args:
            addrs (bool, optional): Load addresses? Defaults to True.
            prefixes (bool, optional): Load prefixes? Defaults to True.
            address_filter (_type_, optional): Filter to use with addresses.
              Defaults to None.
            domain_filter (_type_, optional): Filter to use with prefixes.
              Defaults to None.
        """
        super().load()
        if addrs:
            self.job.log_info(message="Starting to load IP addresses")
            self._load_ip_addresses(address_filter, domain_filter)
        if prefixes:
            self.job.log_info(message="Starting to load prefixes")
            self._load_ip_prefixes(address_filter)

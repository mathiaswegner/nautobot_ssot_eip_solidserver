"""Adapter to collect IP addresses and prefixes from Solidserver
and creates DiffSync models
"""
from nautobot_ssot_eip_solidserver.diffsync.models.solidserver import \
    SolidserverIPAddress, SolidserverIPPrefix
from nautobot_ssot_eip_solidserver.utils import ssutils
from diffsync import DiffSync
from diffsync.exceptions import ObjectAlreadyExists


class SolidserverAdapter(DiffSync):
    """DiffSync adapter for Solidserver
    """

    address = SolidserverIPAddress
    prefix = SolidserverIPPrefix

    top_level = ["address", "prefix"]

    def __init__(self, *args, job=None, conn: ssutils.SolidServerAPI,
                 sync=None, **kwargs):
        """Initialize the Solidserver DiffSync adapter."""
        super().__init__(*args, **kwargs)
        self.job = job
        self.conn = conn
        self.sync = sync

    def _process_ipv4_addr(self, each_addr):
        """Convert one Solidserver IP4 record into a diffsync model

        Args:
            each_addr (dict): the Solidserver address record

        Returns:
            SolidserverIPAddress: the diffsync model
        """
        try:
            subnet_size = str(bin(int(
                each_addr.get('subnet_size')))).lstrip('0b')
            cidr_size = 32 - subnet_size.count('0')
        except (ValueError, KeyError):
            cidr_size = None
        try:
            descr = ssutils.unpack_class_params(
                each_addr['ip_class_parameters']).get('__eip_description')
        except (ValueError, KeyError):
            descr = ""
        except AttributeError:
            message = f"ip_class params: {each_addr['ip_class_parameters']}"
            self.job.log_debug(message=message)
            descr = ""
        new_addr = self.address(
            dns_name=each_addr.get('name'),
            description=descr,
            address=each_addr.get('hostaddr'),
            # status=status,
            nnn_id=int(each_addr.get('ip_id')),
            subnet_size=cidr_size
                    )
        if not new_addr.nnn_id and not new_addr.dns_name:
            return None, None
        return new_addr, each_addr.get('subnet_id', -1)

    def _process_ipv6_addr(self, each_addr):
        """Convert one Solidserver IP6 record into a diffsync model

        Args:
            each_addr (dict): the Solidserver address record

        Returns:
            SolidserverIPAddress: the diffsync model
        """
        try:
            cidr_size = each_addr.get('subnet6_prefix')
        except (ValueError, KeyError):
            cidr_size = None
        try:
            descr = ssutils.unpack_class_params(
                each_addr['ip6_class_parameters']).get('__eip_description')
        except (ValueError, KeyError):
            descr = ""
        except AttributeError:
            self.job.log_debug(
                f"ip_class params: {each_addr['ip6_class_parameters']}")
            descr = ""
        new_addr = self.address(
            dns_name=each_addr.get('ip6_name', ''),
            description=descr,
            address=each_addr.get('hostaddr'),
            nnn_id=int(each_addr.get('ip6_id')),
            subnet_size=cidr_size
        )
        if not new_addr.nnn_id and not new_addr.dns_name:
            return None, None
        return new_addr, each_addr.get('subnet6_id', -1)

    def _process_ipv4_prefix(self, each_prefix):
        """Convert one Solidserver IP4 record into a diffsync model

        Args:
            each_prefix (dict): the Solidserver prefix record

        Returns:
            SolidserverPrefix: the diffsync model
        """
        subnet_size = str(bin(int(
            each_prefix.get('subnet_size', '0')))).lstrip('0b')
        cidr_size = 32 - subnet_size.count('0')
        try:
            descr = ssutils.unpack_class_params(
                each_prefix['ip_class_parameters']).get('__eip_description')
        except (ValueError, KeyError):
            descr = ""
        new_prefix = self.prefix(
            description=descr,
            prefix=each_prefix.get('start_hostaddr'),
            # status=status,
            nnn_id=int(each_prefix.get('subnet_id')),
            subnet_size=cidr_size
        )
        return new_prefix

    def _process_ipv6_prefix(self, each_prefix):
        """Convert one Solidserver IP6 record into a diffsync model

        Args:
            each_prefix (dict): the Solidserver prefix record

        Returns:
            SolidserverPrefix: the diffsync model
        """
        try:
            descr = ssutils.unpack_class_params(
                each_prefix['ip6_class_parameters']).get('__eip_description')
        except (ValueError, KeyError):
            descr = ""
        new_prefix = self.prefix(
            description=descr,
            prefix=each_prefix.get('start_hostaddr'),
            # status=status,
            nnn_id=int(each_prefix.get('subnet6_id')),
            subnet_size=int(each_prefix.get('subnet6_prefix', 129))
        )
        return new_prefix

    def _load_addresses(self, address_filter=None, domain_filter=None):
        """Run the api queries against Solidserver, using filters if given,
        then convert results into diffsync models

        Args:
            address_filter (str or list, optional): CIDR filter. Defaults to
            None.
            domain_filter (str or list, optional): Domain name filter. Defaults
            to None.

        Returns:
            list: a list of unique prefix IDs collected from parent network
            attribute of addresses
        """
        all_addrs = []
        prefix_ids = []
        if address_filter:
            message = f"Starting to filter addresses with {address_filter}"
            self.job.log_debug(message=message)
            filter_addrs = ssutils.get_addresses_by_network(
                self.conn, address_filter)
            message = f"Got {len(filter_addrs)} back"
            self.job.log_debug(message=message)
            if filter_addrs:
                message = f"address filter {len(filter_addrs)} addrs"
                self.job.log_debug(message=message)
                all_addrs.extend(filter_addrs)
        if domain_filter:
            message = f"Starting to filter addresses with {domain_filter}"
            self.job.log_debug(message=message)
            filter_names = ssutils.get_addresses_by_name(
                self.conn, domain_filter)
            message = f"Got {len(filter_names)} back"
            self.job.log_debug(message=message)
            if filter_names:
                message = f"name filter {len(filter_names)} addrs"
                self.job.log_debug(message=message)
                all_addrs.extend(filter_names)
        if not address_filter and not domain_filter:
            message = "Starting to gather unfiltered addresses"
            self.job.log_debug(message=message)
            all_addrs = ssutils.get_all_addresses(self.conn)
            message = f"no filter {len(all_addrs)}"
            self.job.log_debug(message=message)

        for each_addr in all_addrs:
            if each_addr.get('hostaddr'):
                if each_addr.get('ip_id'):
                    # ipv4
                    new_addr, subnet_id = self._process_ipv4_addr(each_addr)
                elif each_addr.get('ip6_id'):
                    # ipv6
                    new_addr, subnet_id = self._process_ipv6_addr(each_addr)
                if not new_addr:
                    continue
                if subnet_id not in prefix_ids:
                    prefix_ids.append(subnet_id)
                try:
                    self.add(new_addr)
                except ObjectAlreadyExists as err:
                    self.job.log_warning(
                        f"_load_addresses() Unable to load {new_addr.address}"
                        + f" as appears to be a duplicate. {err}")
        return prefix_ids

    def _load_prefixes(self, address_filter=None, subnet_list=None):
        """Run the api queries against Solidserver, using filters if given,
        then convert results into diffsync models

        Args:
            address_filter (str or list, optional): CIDR filter. Defaults to
            None.
            subnet_list (list, optional): If addresses have been loaded,
            this will be a list of the parent network IDs for all of the
            addresses
        """
        all_prefixes = []
        if address_filter:
            filter_prefixes = ssutils.get_prefixes_by_network(
                self.conn, address_filter)
            if filter_prefixes:
                all_prefixes.extend(filter_prefixes)
                message = f"address_filter {len(filter_prefixes)} prefixes"
                self.job.log_debug(message=message)
        if subnet_list:
            self.job.log_debug(message=f"Subnet list {len(subnet_list)}")
            filter_name_prefixes = ssutils.get_prefixes_by_id(
                self.conn, subnet_list)
            if filter_name_prefixes:
                all_prefixes.extend(filter_name_prefixes)
                message = f"name_filter {len(filter_name_prefixes)} prefixes"
                self.job.log_debug(message=message)
        if not address_filter and not subnet_list:
            all_prefixes = ssutils.get_all_prefixes(self.conn)
            message = f"No filter total {len(all_prefixes)} prefixes"
            self.job.log_debug(message=message)

        for each_prefix in all_prefixes:
            if isinstance(each_prefix, list):
                if len(each_prefix) != 1:
                    message = f"Too many prefixes! {each_prefix}"
                    self.job.log_warning(message=message)
                each_prefix = each_prefix[0]
            if each_prefix.get('is_terminal'):
                if each_prefix.get('subnet_id'):
                    # ipv4
                    new_prefix = self._process_ipv4_prefix(each_prefix)
                elif each_prefix.get('subnet6_id'):
                    # ipv6
                    new_prefix = self._process_ipv6_prefix(each_prefix)
                try:
                    self.add(new_prefix)
                except ObjectAlreadyExists as err:
                    self.job.log_warning(
                        f"_load_prefixes() Unable to load {new_prefix.prefix} "
                        + f"/{new_prefix.subnet_size}. {err}")
                    self.job.log_debug(f"prefix: {each_prefix}")

    def load(self, addrs=True, prefixes=True, address_filter=None,
             domain_filter=None):
        """Load data sets and return the populated DiffSync adapter
        objects."""
        prefix_ids = None
        if addrs:
            self.job.log_debug("Starting to load addresses")
            prefix_ids = self._load_addresses(address_filter, domain_filter)
        if prefixes:
            self.job.log_debug("Starting to load prefixes")
            self._load_prefixes(address_filter, prefix_ids)

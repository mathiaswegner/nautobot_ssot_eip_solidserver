"""Job for runnning solidserver to nautobot data sync
"""
import netaddr
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from nautobot.extras.jobs import BooleanVar, IPNetworkVar, StringVar, Job, \
    IntegerVar
from nautobot.ipam.models import IPAddress
from nautobot.ipam.models import Prefix
from nautobot_ssot.jobs.base import DataMapping, DataSource
from nautobot_ssot_eip_solidserver import SSoTEIPSolidServerConfig
from nautobot_ssot_eip_solidserver.utils import ssutils
from nautobot_ssot_eip_solidserver.diffsync.adapters import nautobot, \
    solidserver
from diffsync.enum import DiffSyncFlags
from diffsync.exceptions import ObjectNotCreated

DEFAULT_URL = SSoTEIPSolidServerConfig.default_settings.get('nnn_url')
name = "SSoT EIP Solidserver"


class SolidserverDataSource(DataSource, Job):
    """Solidserver SSoT Data Source."""

    username = StringVar(required=False, label='Username')
    password = StringVar(required=False, label='Password')
    solidserver_url = StringVar(
        required=True,
        default=SSoTEIPSolidServerConfig.default_settings.get('nnn_url'),
        label='SolidServer URL')
    domain_name_filter = StringVar(
        required=False, default='',
        label='Optional domain name filter',
        description='Comma separated list of domains, only used for addresses')
    address_filter = IPNetworkVar(required=False,
                                  label='Optional network filter',
                                  description='Limit sync to a CIDR')
    fetch_addresses = BooleanVar(required=False, default=True,
                                 label="Compare and sync addresses")
    fetch_prefixes = BooleanVar(required=False, default=False,
                                label="Compare and sync prefixes")
    solidserver_timeout = IntegerVar(required=False, default=60,
                                     label="Timeout (sec) for Solidserver")
    debug = BooleanVar(required=False, default=False,
                       description="Enable for verbose debug logging.")

    class Meta:
        """Metadata about job
        """
        name = "Update Nautobot from Solidserver"
        data_source = "Solidserver"
        description = "Sync information from Solidserver to Nautobot"
        commit_default = True
        # field_order = []

    def __init__(self):
        super().__init__()
        self.commit = True

    @classmethod
    def data_mappings(cls):
        """List describing the data mappings involved in this DataSource."""
        return (
            DataMapping("IP Addresses", None, "IP Addresses",
                        reverse("ipam:ipaddress_list")),
            DataMapping("IP Prefixes", None, "IP Prefixes",
                        reverse("ipam:prefix_list")),
        )

    @classmethod
    def config_information(cls):
        """Dictionary describing the configuration of this DataSource."""
        return {
            "SolidSERVER host": settings.PLUGIN_CONFIG.get(
                "nnn_url", "NOT SET!"),
            "SolidSERVER user": settings.PLUGIN_CONFIG.get(
                "nnn_user", "NOT SET!"),
            "Plugin version": SSoTEIPSolidServerConfig.version,
            "Plugin build": SSoTEIPSolidServerConfig.build,
        }

    def lookup_object(self, model_name, unique_id):
        """Look up a Nautobot object based on the DiffSync model name and
        unique ID."""
        obj = None
        try:
            if model_name == "address":
                obj = IPAddress.objects.get(host=unique_id)
            elif model_name == "prefix":
                obj = Prefix.objects.get(prefix=unique_id)
        except ObjectDoesNotExist:
            pass
        return obj

    def log_debug(self, message):
        """Conditionally log a debug message."""
        if self.kwargs.get("debug"):
            super().log_debug(message)

    def load_source_adapter(self, client, domain_list):
        """Method to instantiate and load the SOURCE adapter into
        `self.source_adapter`."""
        self.log_debug(message="Creating Solidserver adapter")
        self.source_adapter = solidserver.SolidserverAdapter(
            job=self, conn=client, sync=self.sync)
        self.log_debug(message="Running Solidserver .load()")
        self.source_adapter.load(addrs=self.kwargs.get('fetch_addresses'),
                                 prefixes=self.kwargs.get('fetch_prefixes'),
                                 address_filter=self.kwargs.get(
                                    'address_filter'),
                                 domain_filter=domain_list)

    def load_target_adapter(self, domain_list):
        """Method to instantiate and load the TARGET adapter into
        `self.target_adapter`."""
        self.log_debug(message="Creating Nautobot adapter")
        self.target_adapter = nautobot.NautobotAdapter(
            job=self, sync=self.sync)
        self.log_debug(message="Starting to run nautobot .load()")
        self.target_adapter.load(addrs=self.kwargs.get('fetch_addresses'),
                                 prefixes=self.kwargs.get('fetch_prefixes'),
                                 address_filter=self.kwargs.get(
                                    'address_filter'),
                                 domain_filter=domain_list)

    # def run(self, data, commit):
    def sync_data(self):
        """SSoT plugin required sync_data method
        Loads both adapters, gets data sets from both, runs diff
        operation and, if commit, sync operation
        """
        try:
            self.log_debug(f"commit {self.commit}")
        except AttributeError:
            self.log_debug("attr error trying to get self.commit")
        if self.kwargs.get('address_filter'):
            try:
                netaddr.IPNetwork(self.kwargs.get('address_filter', ''))
            except (netaddr.core.AddrFormatError, KeyError,
                    AttributeError) as addr_err:
                self.log_failure(message='Address filter is not a CIDR')
                raise ValueError('Address filter is not a CIDR') \
                    from addr_err
        domain_list = []
        if self.kwargs.get('domain_name_filter'):
            domain_list, errors = ssutils.domain_name_prep(self.kwargs.get(
                    'domain_name_filter'))
            if errors:
                for each_err in errors:
                    self.log_failure(message=each_err)
                raise ValueError('Domain filter contains invalid domains')
            message = f"Domain filter list: {domain_list}"
            self.log_debug(message=message)
        self.log_debug(f"Fetch addresses {self.kwargs.get('fetch_addresses')}")
        self.log_debug(f"Fetch prefixes {self.kwargs.get('fetch_prefixes')}")
        self.log_debug(f"CIDR filter {self.kwargs.get('address_filter')}")
        self.log_debug(f"Name filter {self.kwargs.get('domain_name_filter')}")
        self.log_debug(message='Creating Solidserver connection')
        client = ssutils.SolidServerAPI(
            username=self.kwargs.get('username'),
            password=self.kwargs.get('password'),
            base_url=self.kwargs.get('solidserver_url'),
            debug=self.kwargs.get('debug'),
            timeout=self.kwargs.get('solidserver_timeout'))

        self.log_info(message="Collecting data from EIP SOLIDServer")
        self.load_source_adapter(client, domain_list)
        try:
            self.log_debug(
                f"Got {len(self.source_adapter.dict())} objects from SS")
            self.log_debug(f"Keys: {self.source_adapter.dict().keys()}")
            self.log_debug(
                f"Prefixes: {self.source_adapter.dict().get('prefix', '')}")
            self.log_debug(
                f"Addresses: {self.source_adapter.dict().get('address', '')}")
        except AttributeError:
            self.log_debug(message="Couldn't get length from source adapter")
        self.log_info(message="Collecting data from Nautobot")
        self.load_target_adapter(domain_list)
        try:
            self.log_debug(
                f"Got {len(self.target_adapter.dict())} objects from NB")
            self.log_debug(
                f"Keys: {self.target_adapter.dict().keys()}")
            self.log_debug(
                f"Prefixes: {self.target_adapter.dict().get('prefix', '')}")
            self.log_debug(
                f"Addresses: {self.target_adapter.dict().get('address', '')}")
        except AttributeError:
            self.log_debug(message="Couldn't get length from target adapter")
        diffsync_flags = DiffSyncFlags.CONTINUE_ON_FAILURE
        diffsync_flags |= DiffSyncFlags.LOG_UNCHANGED_RECORDS
        diffsync_flags |= DiffSyncFlags.SKIP_UNMATCHED_DST

        self.log_info(message="Calculating diffs...")
        diff = self.source_adapter.diff_to(
            self.target_adapter, flags=diffsync_flags)
        self.sync.diff = diff.dict()
        self.log_info(f"{self.sync.diff}")
        self.log_info(f"Found {len(diff)} differences")

        self.sync.save()

        if not self.kwargs.get('dry_run'):
            self.commit = True
            try:
                self.source_adapter.sync_to(self.target_adapter)
            except ObjectNotCreated as create_err:
                self.log_debug(f"Unable to create object {create_err}")
            self.log_success(message="Sync complete.")


jobs = [SolidserverDataSource]

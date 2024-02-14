"""Utility module for SSoT plugin for EIP Solidserver

Raises:
    AttributeError: _description_
    SolidServerBaseError: _description_
    SolidServerReturnedError: _description_
    SolidServerBaseError: _description_
"""
import urllib.parse
from typing import Any

import netaddr  # type: ignore
import validators  # type: ignore
from diffsync import Diff, DiffSync  # , DiffElement
from diffsync.exceptions import ObjectNotFound
from validators import ValidationError

from nautobot_plugin_ssot_eip_solidserver.diffsync.models.base import (
    SSoTIPAddress,
    SSoTIPPrefix,
)


def unpack_class_params(params):
    """convert class parameters into a dictionary

    Args:
        params (str): the url encoded class parameters

    Returns:
        dict: unencoded and dictified class parameters
    """
    return dict(urllib.parse.parse_qsl(params, keep_blank_values=True))


def generate_ip4_where_clause(cidr: netaddr.IPNetwork) -> str:
    """Take an IPv4 CIDR and return a where statements to find all addresses within a
    given CIDR (where >= first and <= last)

    Args:
        cidr (netaddr.IPNetwork): a CIDR

    Returns:
        str: a where statement for all subnets within a CIDR
    """
    first_addr = str(hex(cidr.first)).lstrip("0x").rjust(8, "0")
    last_addr = str(hex(cidr.last)).lstrip("0x").rjust(8, "0")
    return f"ip_addr >= '{first_addr}' and ip_addr <= '{last_addr}'"


def generate_ip6_where_clause(cidr: netaddr.IPNetwork) -> str:
    """Take an IPv6 CIDR and return a where statements to find all addresses within a
    given CIDR (where >= first and <= last)

    Args:
        cidr (netaddr.IPNetwork): a CIDR

    Returns:
        str: a where statement for all subnets within a CIDR
    """
    first_addr = str(hex(cidr.first)).lstrip("0x").rjust(32, "0")
    last_addr = str(hex(cidr.last)).lstrip("0x").rjust(32, "0")
    return f"ip6_addr >= '{first_addr}' and ip6_addr <= '{last_addr}'"


def get_ip4_subnet_start_and_end_hexes_query(cidr: netaddr.IPNetwork) -> str:
    """return the first and last addresses in a CIDR as a query string
    for the solidserver api

    Args:
        cidr (netaddr.IPNetwork): a CIDR

    Returns:
        str: a query string for all subnets within a CIDR
    """
    first_addr = str(hex(cidr.first)).lstrip("0x").rjust(8, "0")
    last_addr = str(hex(cidr.last)).lstrip("0x").rjust(8, "0")
    return f"start_ip_addr >= '{first_addr}' and end_ip_addr <= '{last_addr}'"


def get_ip6_subnet_start_and_end_hexes_query(cidr: netaddr.IPNetwork) -> str:
    """return the first and last addresses in a CIDR as a query string
    for the solidserver api

    Args:
        cidr (netaddr.IPNetwork): a CIDR

    Returns:
        str: a query string for all subnets within a CIDR
    """
    first_addr = str(hex(cidr.first)).lstrip("0x").rjust(32, "0")
    last_addr = str(hex(cidr.last)).lstrip("0x").rjust(32, "0")
    return f"start_ip6_addr >= '{first_addr}' and end_ip6_addr <= '{last_addr}'"


def domain_name_prep(domain_filter: str) -> tuple[list, list]:
    """ensure correct formatting in domain name filter(s)

    Args:
        domain_filter (str): a comma separated list of domain filters

    Returns:
        list: one list of valid domains, one list of errors
    """
    domain_list = []
    errors = []
    for each_domain in domain_filter.split(","):
        each_domain = each_domain.strip(" ").lstrip(". ")
        try:
            validators.domain(each_domain)
            domain_list.append(each_domain)
        except ValidationError:
            errors.append(f"{each_domain} is not a valid domain")
    return domain_list, errors


def prefix_to_net(prefix: dict[str, Any]) -> netaddr.IPNetwork | None:
    """convert prefix record to netaddr network object

    Args:
        prefix (dict): a solidserver prefix record

    Returns:
        netaddr.IPNetwork or None: a netaddr representation of the prefix
    """
    if prefix.get("subnet_id"):
        binary_size = str(bin(int(prefix.get("subnet_size", 32)))).lstrip("0b")
        size = 32 - binary_size.count("0")
        network = netaddr.IPNetwork(f"{prefix.get('start_hostaddr')}/{size}")
    elif prefix.get("subnet6_id"):
        size = int(prefix.get("subnet6_prefix", 128))
        network = netaddr.IPNetwork(f"{prefix.get('start_hostaddr')}/{size}")
    else:
        return None
    return network


def is_prefix_valid(prefix: SSoTIPPrefix) -> tuple[bool, str]:
    """check if prefix is valid
    Prefixes should have an _id value and a non-zero network value

    Args:
        prefix (SSoTIPPrefix): a prefix record

    Returns:
        tuple[bool, str]: a tuple containing a boolean and an error message
    """
    prefix_is_valid = True
    err = " "
    if prefix.solidserver_addr_id == "0":
        err = f"Skipping {prefix} as it is invalid"
        err = err + f"\naddr_id {prefix.solidserver_addr_id}"
        err = err + f"\nhost {prefix.network}"
        prefix_is_valid = False
    if prefix.network == netaddr.IPNetwork(
        "0.0.0.0/32"
    ) or prefix.network == netaddr.IPNetwork("::/128"):
        err = f"Skipping {prefix} as it is invalid.  "
        err = err + f"addr_id {prefix.solidserver_addr_id}, "
        err = err + f"host {prefix.network}"
        prefix_is_valid = False
    return (prefix_is_valid, err)


def is_addr_valid(
    addr: SSoTIPAddress, addr_type: str
) -> tuple[bool, (str | SSoTIPAddress)]:
    """check if address is valid
    Addresses may have an _id value of 0 if they are free addresses,
    they should have a non-zero host value.

    Args:
        addr (SSoTIPAddress): an address record

    Returns:
        tuple[bool, str]: a tuple containing a boolean and an error message
    """
    addr_is_valid = True
    err = " "
    if addr.solidserver_addr_id == "0" and addr_type == "free":
        addr.status__name = "Unassigned"
        addr.solidserver_addr_id = "unassigned"
    else:
        addr.status__name = "Active"
    if addr.host == netaddr.IPAddress("::0") or addr.host == netaddr.IPAddress(
        "0.0.0.0"
    ):
        err = f"Skipping {addr} as it is invalid.  "
        err = err + f"addr_id {addr.solidserver_addr_id}, "
        err = err + f"host {addr.host}"
        return (False, err)
    return (addr_is_valid, addr)


def filter_diff_for_status(
    diff: Diff, source_adapter: DiffSync, target_adapter: DiffSync
) -> DiffSync:
    """filter diff for status changes

    Args:
        diff (dict): a diffsync diff

    Returns:
        dict: a filtered diff
    """
    for resource_type in ("ipaddress", "prefix"):
        if resource_type in diff.dict().keys():
            for key, value in diff.dict()[resource_type].items():
                try:
                    this_obj = source_adapter.get(obj=resource_type, identifier=key)
                except ObjectNotFound:
                    continue
                if "status__name" in value["+"].keys():
                    if len(value["+"].keys()) == 1:
                        source_adapter.remove(this_obj)
                    try:
                        if "status__name" in value["-"].keys():
                            matching_obj = target_adapter.get(
                                obj=resource_type, identifier=key
                            )
                            this_obj.status__name = matching_obj.status__name
                            source_adapter.update(this_obj)
                    except KeyError:
                        pass
    return source_adapter

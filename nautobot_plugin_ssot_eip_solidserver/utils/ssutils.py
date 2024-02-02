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
from validators import ValidationFailure

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


def iter_ip4_subnet_values_for_like_clause(cidr: netaddr.IPNetwork) -> list[str]:
    """Iterate through a CIDR, returning a list of CIDRs that are
    one bit shorter than the original CIDR

    Args:
        cidr (netaddr.IPNetwork): a CIDR

    Returns:
        list: a list of CIDRs
    """
    search_list = []
    if cidr.prefixlen >= 24:
        # if the cidr is /24 or smaller, return a list with a single where statement
        first_addr = str(hex(cidr.first)).lstrip("0x").rjust(8, "0")
        last_addr = str(hex(cidr.last)).lstrip("0x").rjust(8, "0")
        return [f"ip_addr >= '{first_addr}' and ip_addr <= '{last_addr}'"]
    else:
        # if the cidr is longer than /24, iterate through the various combinations of
        # first three octets and append them to cidr_list
        for each_cidr in cidr.subnet(24):
            first_addr = str(hex(each_cidr.first)).lstrip("0x").rjust(8, "0")
            last_addr = str(hex(each_cidr.last)).lstrip("0x").rjust(8, "0")
            search_list.append(
                f"ip_addr >= '{first_addr}' and ip_addr <= '{last_addr}'"
            )
    return search_list


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


def iter_ip6_subnet_values_for_like_clause(cidr: netaddr.IPNetwork) -> list[str]:
    """Iterate through a CIDR, returning a list of where statements to find all
    addresses within a given /112
    If the cidr is smaller than /112, return a list with a single where statement

    Args:
        cidr (netaddr.IPNetwork): a CIDR

    Returns:
        list: a list of CIDRs
    """
    search_list = []
    if cidr.prefixlen >= 112:
        first_addr = str(hex(cidr.first)).lstrip("0x").rjust(32, "0")
        last_addr = str(hex(cidr.last)).lstrip("0x").rjust(32, "0")
        return [f"ip6_addr >= '{first_addr}' and ip6_addr <= '{last_addr}'"]
    else:
        for each_cidr in cidr.subnet(112):
            first_addr = str(hex(each_cidr.first)).lstrip("0x").rjust(32, "0")
            last_addr = f"{first_addr[:-4]}ffff".rjust(32, "0")
            search_list.append(
                f"ip6_addr >= '{first_addr}' and ip6_addr <= '{last_addr}'"
            )
    return search_list


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
        except ValidationFailure:
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

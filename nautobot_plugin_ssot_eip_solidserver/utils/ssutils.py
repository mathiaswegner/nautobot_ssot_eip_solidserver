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


def unpack_class_params(params):
    """convert class parameters into a dictionary

    Args:
        params (str): the url encoded class parameters

    Returns:
        dict: unencoded and dictified class parameters
    """
    return dict(urllib.parse.parse_qsl(params, keep_blank_values=True))


def iter_subnet_values_for_like_clause(cidr: netaddr.IPNetwork) -> list[str]:
    """Iterate through a CIDR, returning a list of CIDRs that are
    one bit shorter than the original CIDR

    Args:
        cidr (netaddr.IPNetwork): a CIDR

    Returns:
        list: a list of CIDRs
    """
    cidr_list = []
    if cidr.prefixlen <= 24:
        # if the cidr is /24 or shorter, return the first the octets and trailing dot
        cidr_string = str(cidr.ip)[: str(cidr.ip).rindex(".") + 1]
        cidr_list.append(cidr_string)
    else:
        # if the cidr is longer than /24, iterate through the various combinations of
        # first three octets and append them to cidr_list
        for each_cidr in cidr.subnet(24):
            subnet = str(each_cidr.ip)[: str(each_cidr.ip).rindex(".") + 1]
            cidr_list.append(subnet)
    return cidr_list


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
        except validators.utils.ValidationError:
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

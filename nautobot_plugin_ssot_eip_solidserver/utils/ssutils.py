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
from netaddr import AddrFormatError

from nautobot_plugin_ssot_eip_solidserver.utils.ssapi import SolidServerAPI

LIMIT = 1000  # limit how many solidserver objects to fetch at once


def unpack_class_params(params):
    """convert class parameters into a dictionary

    Args:
        params (str): the url encoded class parameters

    Returns:
        dict: unencoded and dictified class parameters
    """
    return dict(urllib.parse.parse_qsl(params, keep_blank_values=True))


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


def get_prefixes_by_id(nnn: SolidServerAPI, subnet_list: list[str]) -> list[Any]:
    """take a list of unique ids, fetch them from solidserver

    Args:
        nnn (SolidServerAPI): connected solidserver session
        subnet_list (list): a list of subnet IDs

    Returns:
        list: a list of prefix resources
    """
    prefixes = []
    params: dict[str, int | str] = {"LIMIT": LIMIT}
    for each_id in subnet_list:
        nnn.job.log_debug(f"fetching Solidserver prefix id {each_id}")
        params["subnet_id"] = each_id
        this_prefix = nnn.generic_api_action(
            api_action="ip_block_subnet_info", http_action="get", params=params
        )
        if this_prefix:
            prefixes.append(this_prefix)
        else:
            params["subnet6_id"] = each_id
            this_prefix = nnn.generic_api_action(
                api_action="ip6_block6_subnet6_info", http_action="get", params=params
            )
            prefixes.append(this_prefix)
    return prefixes


def get_all_prefixes(nnn: SolidServerAPI) -> list[Any]:
    """Get all IP prefixes from solidserver

    Args:
        nnn (SolidServerAPI): a connected solidserver session

    Returns:
        list: a list of all prefix resources
    """
    prefixes: list[Any] = []
    params = {"LIMIT": LIMIT}
    for action in ["ip_block_subnet_list", "ip6_block6_subnet6_list"]:
        offset = 0
        params["offset"] = offset
        not_done = True
        while not_done:
            partial_result = nnn.generic_api_action(action, "get", params)
            if len(partial_result) < LIMIT:
                not_done = False
            offset = params.get("offset") or 0
            offset += LIMIT
            params["offset"] = offset
            prefixes.extend(partial_result)
            nnn.job.log_debug(f"got {len(partial_result)} objects, offset is {offset}")
            nnn.job.log_debug(f"result has {len(prefixes)}")
        nnn.job.log_debug(f"done iterating {action}, {len(prefixes)} records found")
    return prefixes


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


def get_prefixes_by_network(nnn: SolidServerAPI, cidr: str) -> list[Any]:
    """Test a list of prefixes from the NNN session against a CIDR to see if
    the prefix is contained within the CIDR

    Args:
        nnn (SolidServerAPI): Connected API session to SolidServer
        cidr (str): A CIDR

    Returns:
        List: a list of prefixes that are subnets of the CIDR
    """
    filtered_prefixes = []
    all_prefixes = get_all_prefixes(nnn)
    filter_cidr = netaddr.IPNetwork(cidr)
    for each_prefix in all_prefixes:
        network = None
        try:
            network = prefix_to_net(each_prefix)
            print(network)
        except (ValueError, AddrFormatError):
            name = each_prefix.get("subnet_name", "")
            if not name:
                name = each_prefix.get("subnet6_name", "")
            nnn.job.log_debug(f"netaddr couldn't convert {name} to a network")
            continue
        if network in filter_cidr:
            filtered_prefixes.append(each_prefix)
    return filtered_prefixes


def get_addresses_by_network(nnn: SolidServerAPI, cidr: netaddr.IPNetwork) -> list[Any]:
    """Run queries for each address in a CIDR

    Args:
        nnn (SolidServerAPI): a connected solidserver api session
        cidr (str): a cidr

    Returns:
        list: a list of address models
    """
    ss_addrs = []
    nnn.job.log_debug("Starting get addresses by network")
    filter_cidr = netaddr.IPNetwork(cidr)
    action = "unset"
    if filter_cidr.version == 4:
        action = "ip_address_list"
    elif filter_cidr.version == 6:
        action = "ip6_address6_list"
    params: dict[str, str | int] = {"LIMIT": LIMIT}
    for each_addr in cidr.iter_hosts():
        nnn.job.log_debug(f"fetching Solidserver address for {each_addr}")
        params["WHERE"] = f"hostaddr='{each_addr}'"
        this_address = nnn.generic_api_action(
            api_action=action, http_action="get", params=params
        )
        if this_address:
            if isinstance(this_address, list):
                ss_addrs.extend(this_address)
            else:
                ss_addrs.append(this_address)
    return ss_addrs


def get_addresses_by_name(nnn: SolidServerAPI, domain_list: list[str]) -> list[Any]:
    """Iterate through list of domains, running query once per list

    Args:
        nnn (SolidServerAPI): connected Solidserver session
        domain_list (list): list of domain filters

    Returns:
        list: a list of solidserver records
    """
    ss_addrs = []
    for each_domain in domain_list:
        each_domain = f"{each_domain}"
        nnn.job.log_debug(f"fetching Solidserver address batch for {each_domain}")
        these_addrs = get_solidserver_batch(nnn, each_domain)
        if these_addrs:
            if isinstance(these_addrs, list):
                ss_addrs.extend(these_addrs)
            else:
                ss_addrs.append(these_addrs)
    return ss_addrs


def get_solidserver_batch(nnn: SolidServerAPI, domain_name: str) -> list[Any]:
    """Run a query for all addresses matching a single domain nname

    Args:
        nnn (SolidServerAPI): connected Solidserver session
        domain_name (str): a domain name

    Returns:
        list: a list of solidserver records
    """
    params: dict[str, str | int] = {"limit": LIMIT}
    result: list[Any] = []
    count_action: dict[str, tuple[str, str]] = {
        "ip_address_list": ("ip_address_count", "name"),
        "ip6_address6_list": ("ip6_address6_count", "ip6_name"),
    }

    for action in ["ip_address_list", "ip6_address6_list"]:
        offset = 0
        params["offset"] = offset
        params["WHERE"] = (
            f"{count_action.get(action, ('not found', 'not found'))[1]} LIKE"
            f" '%.{domain_name}'"
        )
        nnn.job.log_info(f"starting to process {action} for {domain_name}")
        nnn.job.log_debug(f"WHERE clause is {params.get('WHERE')}")
        not_done = True
        while not_done:
            partial_result = nnn.generic_api_action(action, "get", params)
            if len(partial_result) < LIMIT:
                not_done = False
            offset += LIMIT
            params["offset"] = offset
            result.extend(partial_result)
            nnn.job.log_debug(f"got {len(partial_result)} objects, offset is {offset}")
            nnn.job.log_debug(f"result has {len(result)} total objects")
        nnn.job.log_debug(f"done iterating {action}, {len(result)} records found")
    return result


def get_all_addresses(nnn: SolidServerAPI) -> list[Any]:
    """get addresses from solidserver (by version and batched)
    load address data into nnnrecord objects, load nnnrecord
    objects into dictionary with unique ID as key

    Args:
        nnn (SolidServerAPI): SolidServerAPI object with
        url and credentials loaded

    Returns:
        dict: solidserver unique ID as key, nnnRecord object
        as value
    """
    addrs = []
    params = {"limit": LIMIT}
    count_action = {
        "ip_address_list": "ip_address_count",
        "ip6_address6_list": "ip6_address6_count",
    }
    for action in ["ip_address_list", "ip6_address6_list"]:
        offset = 0
        params["offset"] = offset
        nnn.job.log_info("starting to process %s", action)
        not_done = True
        count = nnn.generic_api_action(
            count_action.get(action, "ip_address_count"), "get", {}
        )
        nnn.job.log_debug(f"Expecting {count[0].get('total')} total addresses")
        # nnn_tqdm = tqdm(total=int(count[0].get('total')))
        result: list[Any] = []
        while not_done:
            partial_result = nnn.generic_api_action(action, "get", params)
            if len(partial_result) < LIMIT:
                not_done = False
            # nnn_tqdm.update(len(partial_result))
            offset += LIMIT
            params["offset"] = offset
            result.extend(partial_result)
            nnn.job.log_debug(f"got {len(partial_result)} objects, offset is {offset}")
            nnn.job.log_debug(f"result has {len(result)} objects")
        nnn.job.log_debug(f"done iterating {action}, {len(result)} records found")
        addrs.extend(result)
    nnn.job.log_debug(f"total addr count for all addresses is {len(addrs)}")
    return addrs

"""Quick and dirty wrapper for solidserver API"""
import base64
import json
import urllib.parse
from typing import Any

import certifi
import netaddr  # type: ignore
import requests
from nautobot.extras.jobs import Job  # type: ignore
from netaddr import AddrFormatError

from nautobot_plugin_ssot_eip_solidserver.constants import LIMIT, SOLIDSERVER_URL
from nautobot_plugin_ssot_eip_solidserver.utils import ssutils


class SolidServerBaseError(Exception):
    """Base error"""


class SolidServerUsageError(SolidServerBaseError):
    """SolidServer returned an error"""


class SolidServerReturnedError(SolidServerBaseError):
    """SolidServer returned an error"""


class SolidServerValueNotFoundError(SolidServerBaseError):
    """No value found for requested attr/categ"""


class SolidServerNotConnectedError(SolidServerBaseError):
    """Not connected or failed to connect"""


class AuthFailure(Exception):
    """Exception raised when authenticating to on-prem CVP fails."""

    def __init__(self, error_code, message):
        """Populate exception information."""
        self.expression = error_code
        self.message = message
        super().__init__(self.message)


class SolidServerAPI:
    """A class to interact with the SolidServer API"""

    def __init__(
        self,
        job: Job,
        username: str = "",
        password: str = "",
        base_url: str = SOLIDSERVER_URL,
        sslverify: bool = True,
        **kwargs,
    ) -> None:
        """Constructor.  We'll just store some objects in a dictionary via
        kwargs"""
        self.__attributes: dict[Any, Any] = {}
        self.__sslverify: bool = sslverify
        self.job = job
        if kwargs:
            self.__attributes.update(kwargs)
        try:
            parsed_url = urllib.parse.urlparse(base_url.removesuffix("/"))
        except AttributeError as att_err:
            raise AttributeError(f"{base_url} is not a valid url") from att_err
        if not parsed_url.scheme:
            self.base_url = "https://" + parsed_url.geturl()
        else:
            self.base_url = parsed_url.geturl()
        self.job.log_debug(f"base url is {self.base_url}")
        self.connected = False
        self.session = requests.Session()
        if username:
            user64 = base64.b64encode(username.encode("ascii")) or ""
            try:
                pw64 = base64.b64encode(password.encode("ascii")) or ""
            except AttributeError:
                pw64 = ""
            self.__headers = {"""X-IPM-Username""": user64, """X-IPM-Password""": pw64}
            self.session.headers.update({})
        verify = self.__attributes.get("verify") or None
        if verify:
            if verify == "certifi":
                self.session.verify = certifi.where()
            else:
                self.session.verify = verify
            self.job.log_debug(f"session CA bundle is {self.session.verify}")
        if not self.__attributes.get("timeout"):
            self.__attributes["timeout"] = 60

    def close(self) -> None:
        """close requests session"""
        self.session.close()

    def url(self, path: str) -> str:
        """generate full url"""
        if not path.startswith("/"):
            path = "/" + path
        if not path.startswith("/rest"):
            path = "/rest" + path
        return self.base_url + path

    def set_attr(self, **kwargs) -> None:
        """set arbitrary attribute"""
        for name, value in kwargs.items():
            self.__attributes[name] = value

    def get_attr(self, arg: Any) -> Any | None:
        """get any one attribute, return value"""
        return self.__attributes.get(arg)

    def get_attr_list(self, *args) -> list[Any]:
        """get any attributes using args, returning a list of attributes"""
        attrs = []
        for each_arg in args:
            attrs.append(self.__attributes.get(each_arg))
        return attrs

    def get_attribute_keys(self):
        """returns a list of attribute names"""
        return self.__attributes.keys()

    def get_attribute_dict(self) -> dict[Any, Any]:
        """returns all attr names and values"""
        return self.__attributes

    def generic_api_action(
        self,
        api_action: str,
        http_action: str = "get",
        params: dict[str, Any] | None = None,
        data=None,
    ) -> list[Any] | Any:
        """Generic API action, returns json response

        Args:
            api_action (str): API action to perform
            http_action (str, optional): HTTP action to perform. Defaults to "get".
            params (dict, optional): Parameters to pass to API. Defaults to None.
            data (dict, optional): Data to pass to API. Defaults to None.
            debug (bool, optional): Print debug info. Defaults to False.

        Raises:
            SolidServerBaseError: [description]
            SolidServerReturnedError: [description]

        Returns:
            dict: json response in dict form
        """
        url = self.url(api_action)

        self.job.log_debug(f"url {url}")

        if http_action == "post":
            response = self.session.post(
                url,
                params=params,
                data=data,
                headers=self.__headers,
                verify=self.__sslverify,
                timeout=self.__attributes["timeout"],
            )
        elif http_action == "get":
            self.job.log_debug(f"params {params}")
            self.job.log_debug(f"data {data}")
            self.job.log_debug(f"headers {self.__headers}")
            self.job.log_debug(f"ssl verify {self.__sslverify}")
            response = self.session.get(
                url,
                params=params,
                data=data,
                headers=self.__headers,
                verify=self.__sslverify,
                timeout=self.__attributes["timeout"],
            )
        elif http_action == "put":
            response = self.session.put(
                url,
                params=params,
                data=data,
                headers=self.__headers,
                verify=self.__sslverify,
                timeout=self.__attributes["timeout"],
            )
        elif http_action == "delete":
            response = self.session.delete(
                url,
                params=params,
                data=data,
                headers=self.__headers,
                verify=self.__sslverify,
                timeout=self.__attributes["timeout"],
            )
        elif http_action == "options":
            response = self.session.options(
                url,
                params=params,
                data=data,
                headers=self.__headers,
                verify=self.__sslverify,
                timeout=self.__attributes["timeout"],
            )
        else:
            raise SolidServerBaseError("Not yet implemented")

        if not response.ok:
            self.job.log_debug(f"response ok {response.ok}")
            self.job.log_debug(f"response code {response.status_code}")
            self.job.log_debug(f"response reason {response.reason}")
            self.job.log_debug(f"response raw {response.raw}")
            self.job.log_debug(f"response url {response.url}")
            raise SolidServerReturnedError(response.text)

        if response.status_code == 204 or response.text == " ":
            return []
        try:
            r_text = json.loads(response.text)
        except json.decoder.JSONDecodeError as json_err:
            raise SolidServerBaseError(
                f"Error decoding json {response.text}"
            ) from json_err
        return r_text

    def get_prefixes_by_id(self, subnet_list: list[str]) -> list[Any]:
        """take a list of unique ids, fetch them from solidserver

        Args:
            subnet_list (list): a list of subnet IDs

        Returns:
            list: a list of prefix resources
        """
        prefixes = []
        params: dict[str, int | str] = {"LIMIT": LIMIT}
        for each_id in subnet_list:
            self.job.log_debug(f"fetching Solidserver prefix id {each_id}")
            params["subnet_id"] = each_id
            this_prefix = self.generic_api_action(
                api_action="ip_block_subnet_info", http_action="get", params=params
            )
            if this_prefix:
                prefixes.append(this_prefix)
            else:
                params["subnet6_id"] = each_id
                this_prefix = self.generic_api_action(
                    api_action="ip6_block6_subnet6_info",
                    http_action="get",
                    params=params,
                )
                prefixes.append(this_prefix)
        return prefixes

    def get_all_addresses(self) -> list[Any]:
        """get addresses from solidserver (by version and batched)
        load address data into nnnrecord objects, load nnnrecord
        objects into dictionary with unique ID as key

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
            self.job.log_info("starting to process %s", action)
            not_done = True
            count = self.generic_api_action(
                count_action.get(action, "ip_address_count"), "get", {}
            )
            self.job.log_debug(f"Expecting {count[0].get('total')} total addresses")
            result: list[Any] = []
            while not_done:
                partial_result = self.generic_api_action(action, "get", params)
                if len(partial_result) < LIMIT:
                    not_done = False
                offset += LIMIT
                params["offset"] = offset
                result.extend(partial_result)
                self.job.log_debug(
                    f"got {len(partial_result)} objects, offset is {offset}"
                )
                self.job.log_debug(f"result has {len(result)} objects")
            self.job.log_debug(f"done iterating {action}, {len(result)} records found")
            addrs.extend(result)
        self.job.log_debug(f"total addr count for all addresses is {len(addrs)}")
        return addrs

    def get_all_prefixes(self) -> list[Any]:
        """Get all IP prefixes from solidserver

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
                partial_result = self.generic_api_action(action, "get", params)
                if len(partial_result) < LIMIT:
                    not_done = False
                offset = params.get("offset") or 0
                offset += LIMIT
                params["offset"] = offset
                prefixes.extend(partial_result)
                self.job.log_debug(
                    f"got {len(partial_result)} objects, offset is {offset}"
                )
                self.job.log_debug(f"result has {len(prefixes)}")
            self.job.log_debug(
                f"done iterating {action}, {len(prefixes)} records found"
            )
        return prefixes

    def get_solidserver_batch(self, domain_name: str) -> list[Any]:
        """Run a query for all addresses matching a single domain nname

        Args:
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
            self.job.log_info(f"starting to process {action} for {domain_name}")
            self.job.log_debug(f"WHERE clause is {params.get('WHERE')}")
            not_done = True
            while not_done:
                partial_result = self.generic_api_action(action, "get", params)
                if len(partial_result) < LIMIT:
                    not_done = False
                offset += LIMIT
                params["offset"] = offset
                result.extend(partial_result)
                self.job.log_debug(
                    f"got {len(partial_result)} objects, offset is {offset}"
                )
                self.job.log_debug(f"result has {len(result)} total objects")
            self.job.log_debug(f"done iterating {action}, {len(result)} records found")
        return result

    def get_addresses_by_name(self, domain_list: list[str]) -> list[Any]:
        """Iterate through list of domains, running query once per list

        Args:
            domain_list (list): list of domain filters

        Returns:
            list: a list of solidserver records
        """
        ss_addrs = []
        for each_domain in domain_list:
            each_domain = f"{each_domain}"
            self.job.log_debug(f"fetching Solidserver address batch for {each_domain}")
            these_addrs = self.get_solidserver_batch(each_domain)
            if these_addrs:
                if isinstance(these_addrs, list):
                    ss_addrs.extend(these_addrs)
                else:
                    ss_addrs.append(these_addrs)
        return ss_addrs

    def get_addresses_by_network(self, cidr: netaddr.IPNetwork) -> list[Any]:
        """Run queries for each address in a CIDR

        Args:
            cidr (str): a cidr

        Returns:
            list: a list of address models
        """
        ss_addrs = []
        self.job.log_debug("Starting get addresses by network")
        sub_cidrs: list[str] = ssutils.iter_subnet_values_for_like_clause(cidr)
        action = "unset"
        if cidr.version == 4:
            action = "ip_address_list"
        elif cidr.version == 6:
            action = "ip6_address6_list"
        params: dict[str, str | int] = {"LIMIT": LIMIT}
        for each_cidr in sub_cidrs:
            self.job.log_debug(f"fetching Solidserver address for {each_cidr}")
            params["WHERE"] = f"hostaddr like '{each_cidr}%'"
            this_address = self.generic_api_action(
                api_action=action, http_action="get", params=params
            )
            if this_address:
                if isinstance(this_address, list):
                    for each_addr in this_address:
                        if each_addr.get("hostaddr") in cidr:
                            ss_addrs.append(each_addr)
                else:
                    if this_address.get("hostaddr") in cidr:
                        ss_addrs.append(this_address)
        return ss_addrs

    def get_prefixes_by_network(self, cidr: str) -> list[Any]:
        """Test a list of prefixes from the NNN session against a CIDR to see if
        the prefix is contained within the CIDR

        Args:
            nnn (SolidServerAPI): Connected API session to SolidServer
            cidr (str): A CIDR

        Returns:
            List: a list of prefixes that are subnets of the CIDR
        """
        filtered_prefixes = []
        all_prefixes = self.get_all_prefixes()
        filter_cidr = netaddr.IPNetwork(cidr)
        for each_prefix in all_prefixes:
            network = None
            try:
                network = ssutils.prefix_to_net(each_prefix)
                print(network)
            except (ValueError, AddrFormatError):
                name = each_prefix.get("subnet_name", "")
                if not name:
                    name = each_prefix.get("subnet6_name", "")
                self.job.log_debug(f"netaddr couldn't convert {name} to a network")
                continue
            if network in filter_cidr:
                filtered_prefixes.append(each_prefix)
        return filtered_prefixes

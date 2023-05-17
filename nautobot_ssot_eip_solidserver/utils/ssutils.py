"""Utility module for SSoT plugin for EIP Solidserver

Raises:
    AttributeError: _description_
    SolidServerBaseError: _description_
    SolidServerReturnedError: _description_
    SolidServerBaseError: _description_
"""
import base64
import json
import logging
import pathlib
import sys
import urllib.parse
import certifi
import netaddr
import requests
import validators

DOMAINS = ('.router.private.upenn.edu', '.dccs.private.upenn.edu',
           '.wlan.private.upenn.edu', '.isc.private.upenn.edu', '.magpi.net',
           '.router.upenn.edu', '.isc.upenn.edu', '.nnn.upenn.edu',
           '.dccs.upenn.edu', '.net.isc.upenn.edu')
LIMIT = 1000
LOGGER = logging.Logger('ssot.solidserver')


def get_version():
    """get the version with build number

    Returns:
        str: version with build
    """
    version_dir = pathlib.Path(__file__).parent
    try:
        with (version_dir / "_version.py").open("r") as version_file:
            lines = version_file.readlines()
            for line in lines:
                if "__version__" in line:
                    return line.split(" ")[-1].rstrip("'").strip("\n' ")
            return "Build unknown"
    except FileNotFoundError:
        return "Build unknown"


def enable_ss_debug():
    """Setting up debugging for solidserver
    """
    logging.basicConfig(
        stream=sys.stdout,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    LOGGER.setLevel(logging.DEBUG)


def unpack_class_params(params):
    """convert class parameters into a dictionary

    Args:
        params (str): the url encoded class parameters

    Returns:
        dict: unencoded and dictified class parameters
    """
    return dict(urllib.parse.parse_qsl(params, keep_blank_values=True))


def domain_name_prep(domain_filter):
    """ensure correct formattincg in domain name filter(s)

    Args:
        domain_filter (str): a comma separated list of domain filters

    Returns:
        list: one list of valid domains, one list of errors
    """
    domain_list = []
    errors = []
    for each_domain in domain_filter.split(','):
        each_domain = each_domain.strip(' ').lstrip('. ')
        try:
            validators.domain(each_domain)
            domain_list.append(each_domain)
        except validators.ValidationFailure:
            errors.append(f"{each_domain} is not a valid domain")
    return domain_list, errors


def get_prefixes_by_id(nnn, subnet_list):
    """take a list of unique ids, fetch them from solidserver

    Args:
        nnn (SolidServerAPI): connected solidserver session
        subnet_list (list): a list of subnet IDs

    Returns:
        list: a list of prefix resources
    """
    prefixes = []
    params = {'LIMIT': LIMIT}
    for each_id in subnet_list:
        LOGGER.debug("fetching Solidserver prefix id %s", each_id)
        params['subnet_id'] = each_id
        this_prefix = nnn.generic_api_action('ip_block_subnet_info', 'get',
                                             params=params)
        if this_prefix:
            prefixes.append(this_prefix)
        else:
            params['subnet6_id'] = each_id
            this_prefix = nnn.generic_api_action('ip6_block6_subnet6_info',
                                                 'get', params=params)
            prefixes.append(this_prefix)
    return prefixes


def get_all_prefixes(nnn):
    """Get all IP prefixes from solidserver

    Args:
        nnn (SolidServerAPI): a connected solidserver session

    Returns:
        list: a list of all prefix resources
    """
    prefixes = []
    params = {'LIMIT': LIMIT}
    for action in ['ip_block_subnet_list', 'ip6_block6_subnet6_list']:
        params['offset'] = 0
        not_done = True
        while not_done:
            partial_result = nnn.generic_api_action(action, 'get', params)
            if len(partial_result) < LIMIT:
                not_done = False
            offset = params.get('offset')
            params['offset'] = offset + LIMIT
            prefixes.extend(partial_result)
            LOGGER.debug('got %s objects, offset is %s',
                         len(partial_result), offset)
            LOGGER.debug('result has %s total objects', len(prefixes))
        LOGGER.debug('done iterating %s, %s records found', action,
                     len(prefixes))
    return prefixes


def prefix_to_net(prefix):
    """convert prefix record to netaddr network object

    Args:
        prefix (dict): a solidserver prefix record

    Returns:
        netaddr.IPNetwork or None: a netaddr representation of the prefix
    """
    if prefix.get('subnet_id'):
        binary_size = str(bin(int(prefix.get('subnet_size')))).lstrip('0b')
        size = 32 - binary_size.count('0')
        network = netaddr.IPNetwork(f"{prefix.get('start_hostaddr')}/{size}")
    elif prefix.get('subnet6_id'):
        size = prefix.get('subnet6_prefix')
        network = netaddr.IPNetwork(f"{prefix.get('start_hostaddr')}/{size}")
    else:
        return None
    return network


def get_prefixes_by_network(nnn, cidr):
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
        except (ValueError, netaddr.core.AddrFormatError):
            name = each_prefix.get('subnet_name', '')
            if not name:
                name = each_prefix.get('subnet6_name', '')
            LOGGER.debug(f"netaddr couldn't convert {name} to a network")
            continue
        if network in filter_cidr:
            filtered_prefixes.append(each_prefix)
    return filtered_prefixes


def get_addresses_by_network(nnn, cidr):
    """Run queries for each address in a CIDR

    Args:
        nnn (SolidServerAPI): a connected solidserver api session
        cidr (str): a cidr

    Returns:
        list: a list of address models
    """
    ss_addrs = []
    LOGGER.debug("Starting get addresses by network")
    filter_cidr = netaddr.IPNetwork(cidr)
    if filter_cidr.version == 4:
        action = 'ip_address_list'
    elif filter_cidr.version == 6:
        action = 'ip6_address6_list'
    params = {'LIMIT': LIMIT}
    for each_addr in cidr.iter_hosts():
        LOGGER.debug("fetching Solidserver address for %s", each_addr)
        params['WHERE'] = f"hostaddr='{each_addr}'"
        this_address = nnn.generic_api_action(action, 'get', params)
        if this_address:
            if isinstance(this_address, list):
                ss_addrs.extend(this_address)
            else:
                ss_addrs.append(this_address)
    return ss_addrs


def get_addresses_by_name(nnn, domain_list):
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
        LOGGER.debug("fetching Solidserver address batch for %s", each_domain)
        these_addrs = get_solidserver_batch(nnn, each_domain)
        if these_addrs:
            if isinstance(these_addrs, list):
                ss_addrs.extend(these_addrs)
            else:
                ss_addrs.append(these_addrs)
    return ss_addrs


def get_solidserver_batch(nnn, domain_name):
    """Run a query for all addresses matching a single domain nname

    Args:
        nnn (SolidServerAPI): connected Solidserver session
        domain_name (str): a domain name

    Returns:
        list: a list of solidserver records
    """
    params = {'limit': LIMIT}
    result = []
    count_action = {'ip_address_list': ('ip_address_count', 'name'),
                    'ip6_address6_list': ('ip6_address6_count', 'ip6_name')}
    for action in ['ip_address_list', 'ip6_address6_list']:
        params['offset'] = 0
        params['WHERE'] = \
            f"{count_action.get(action)[1]} LIKE '%.{domain_name}'"
        LOGGER.info('starting to process %s for %s', action, domain_name)
        LOGGER.debug('WHERE clause is %s', params.get('WHERE'))
        not_done = True
        print(params)
        while not_done:
            partial_result = nnn.generic_api_action(action, 'get', params)
            print(len(partial_result))
            if len(partial_result) < LIMIT:
                not_done = False
            offset = params.get('offset')
            params['offset'] = offset + LIMIT
            result.extend(partial_result)
            LOGGER.debug('got %s objects, offset is %s',
                         len(partial_result), offset)
            LOGGER.debug('result has %s total objects', len(result))
        LOGGER.debug('done iterating %s, %s records found', action,
                     len(result))
    return result


def get_all_addresses(nnn):
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
    params = {'limit': LIMIT}
    count_action = {'ip_address_list': 'ip_address_count',
                    'ip6_address6_list': 'ip6_address6_count'}
    for action in ['ip_address_list', 'ip6_address6_list']:
        params['offset'] = 0
        LOGGER.info('starting to process %s', action)
        not_done = True
        count = nnn.generic_api_action(count_action.get(action), 'get', {})
        LOGGER.debug('Expecting %s total addresses', count[0].get('total'))
        # nnn_tqdm = tqdm(total=int(count[0].get('total')))
        result = []
        while not_done:
            partial_result = nnn.generic_api_action(action, 'get', params)
            if len(partial_result) < LIMIT:
                not_done = False
            # nnn_tqdm.update(len(partial_result))
            offset = params.get('offset')
            params['offset'] = offset + LIMIT
            result.extend(partial_result)
            LOGGER.debug('got %s objects, offset is %s',
                         len(partial_result), offset)
            LOGGER.debug('result has %s objects', len(result))
        LOGGER.debug('done iterating %s, %s records found', action,
                     len(result))
        addrs.extend(result)
    LOGGER.debug('total addr count for all addresses is %s', len(addrs))
    return addrs


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


class SolidServerAPI():
    """A class to interact with the SolidServer API"""

    def __init__(self, username: str = None, password: str = None,
                 base_url: str = "https://dev.nnn.upenn.edu",
                 sslverify: bool = True, **kwargs):
        """Constructor.  We'll just store some objects in a dictionary via
        kwargs"""
        self.__attributes = {}
        self.__sslverify = sslverify
        self.username = username
        self.password = password
        if kwargs:
            self.__attributes.update(kwargs)
        logging.basicConfig(
            stream=sys.stdout,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        LOGGER.setLevel(logging.WARNING)
        if self.__attributes.get('debug'):
            LOGGER.setLevel(logging.DEBUG)
        try:
            parsed_url = urllib.parse.urlparse(base_url.removesuffix('/'))
        except AttributeError as att_err:
            raise AttributeError(f"{base_url} is not a valid url") from att_err
        if not parsed_url.scheme:
            self.base_url = 'https://' + parsed_url.geturl()
        else:
            self.base_url = parsed_url.geturl()
        LOGGER.debug("base url is %s", self.base_url)
        self.connected = False
        self.session = requests.Session()
        if self.username:
            user64 = base64.b64encode(self.username.encode('ascii')) or ''
            try:
                pw64 = base64.b64encode(self.password.encode('ascii')) or ''
            except AttributeError:
                pw64 = ''
            self.__headers = {
                """X-IPM-Username""": user64,
                """X-IPM-Password""": pw64
            }
            self.session.headers.update({})
        verify = self.__attributes.get('verify') or None
        if verify:
            if verify == 'certifi':
                self.session.verify = certifi.where()
            else:
                self.session.verify = verify
            LOGGER.debug("session CA bundle is %s", self.session.verify)
        if not self.__attributes.get('timeout'):
            self.__attributes['timeout'] = 60

    def set_creds(self, username, password):
        """Set the credentials in the session header"""
        self.username = username
        self.password = password
        user64 = base64.b64encode(self.username.encode('ascii')) or ''
        pw64 = base64.b64encode(self.password.encode('ascii')) or ''
        self.__headers = {
            """X-IPM-Username""": user64,
            """X-IPM-Password""": pw64
        }
        self.session.headers.update({})

    def close(self):
        """close requests session"""
        self.session.close()

    def url(self, path):
        """generate full url"""
        if not path.startswith('/'):
            path = '/' + path
        if not path.startswith('/rest'):
            path = '/rest' + path
        return self.base_url + path

    def set_attr(self, **kwargs):
        """set arbitrary attribute"""
        for name, value in kwargs.items():
            self.__attributes[name] = value

    def get_attr(self, arg):
        """get any one attribute, return value"""
        return self.__attributes.get(arg)

    def get_attr_list(self, *args):
        """get any attributes using args, returning a list of attributes"""
        attrs = []
        for each_arg in args:
            attrs.append(self.__attributes.get(each_arg))
        return attrs

    def get_attribute_keys(self):
        """returns a list of attribute names"""
        return self.__attributes.keys()

    def get_attribute_dict(self):
        """returns all attr names and values"""
        return self.__attributes

    def _generic_api_action(self, api_action, http_action='get', params=None,
                            data=None, debug=False):
        self.generic_api_action(api_action, http_action, params, data, debug)

    def generic_api_action(self, api_action, http_action='get', params=None,
                           data=None, debug=False):
        """
        takes 2 arguments - api action (str) and http action (str)
         - api_action should be an API endpoint, eg /dcim/sites/ or
           circuits/circuits
         - http action should be one of get, post, delete, put, or patch
        optionally takes data argument
        optionally takes url_params ???? maybe not for SolidServer,
        what format?
        build a generic action sending url
        makes request to api
        raises SolidServerReturnedError or SolidServerValueNotFoundError if
        appropriate
        returns result dictionary or json, depending on value of oformat
        """
        url = self.url(api_action)

        if debug:
            print('DEBUG:')
            print(url)
        LOGGER.debug("url %s", url)

        if http_action == 'post':
            response = self.session.post(url, params=params, data=data,
                                         headers=self.__headers,
                                         verify=self.__sslverify,
                                         timeout=self.__attributes['timeout'])
        elif http_action == 'get':
            LOGGER.debug(f"params {params}")
            LOGGER.debug(f"data {data}")
            LOGGER.debug(f"headers {self.__headers}")
            LOGGER.debug(f"ssl verify {self.__sslverify}")
            response = self.session.get(url, params=params, data=data,
                                        headers=self.__headers,
                                        verify=self.__sslverify,
                                        timeout=self.__attributes['timeout'])
        elif http_action == 'put':
            response = self.session.put(url, params=params, data=data,
                                        headers=self.__headers,
                                        verify=self.__sslverify,
                                        timeout=self.__attributes['timeout'])
        elif http_action == 'delete':
            response = self.session.delete(url, params=params, data=data,
                                           headers=self.__headers,
                                           verify=self.__sslverify,
                                           timeout=self.__attributes[
                                               'timeout'])
        elif http_action == 'options':
            response = self.session.options(url, params=params, data=data,
                                            headers=self.__headers,
                                            verify=self.__sslverify,
                                            timeout=self.__attributes[
                                                'timeout'])
        else:
            raise SolidServerBaseError('Not yet implemented')

        if not response.ok:
            LOGGER.debug("response ok %s", response.ok)
            LOGGER.debug("response code %s", response.status_code)
            LOGGER.debug("response reason %s", response.reason)
            LOGGER.debug("response raw %s", response.raw)
            LOGGER.debug("response url %s", response.url)
            raise SolidServerReturnedError(response.text)
        if debug:
            print('DEBUG:')
            print('text:_', response.text, '_')
            print('status:', response.status_code)

        if response.status_code == 204 or response.text == ' ':
            return []
        try:
            r_text = json.loads(response.text)
        except json.decoder.JSONDecodeError as json_err:
            raise SolidServerBaseError(
                f'Error decoding json {response.text}') from json_err
        return r_text

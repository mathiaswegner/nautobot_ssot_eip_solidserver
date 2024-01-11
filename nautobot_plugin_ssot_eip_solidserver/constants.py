"""Constants for the nautobot_plugin_ssot_eip_solidserver plugin."""
# IPV4 networks show size by number of free addresses rather than bits of mask.
# This map is used to convert the number of free addresses to a mask length.
IPV4_SUBNET_SIZE_MAP = {
    1: 32,
    2: 31,
    4: 30,
    8: 29,
    16: 28,
    32: 27,
    64: 26,
    128: 25,
    256: 24,
    512: 23,
    1024: 22,
    2048: 21,
    4096: 20,
    8192: 19,
    16384: 18,
    32768: 17,
    65536: 16,
    131072: 15,
    262144: 14,
    524288: 13,
    1048576: 12,
    2097152: 11,
    4194304: 10,
    8388608: 9,
    16777216: 8,
    33554432: 7,
    67108864: 6,
    134217728: 5,
    268435456: 4,
    536870912: 3,
    1073741824: 2,
    2147483648: 1,
}

# Limit the number of objects to retrieve from Solidserver in a single query
LIMIT = 1000

# default URL for Solidserver if something went wrong loading the configuration
SOLIDSERVER_URL = "https://solidserver.example.com"

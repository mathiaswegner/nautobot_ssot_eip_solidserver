# nautobot-plugin-ssot-eip-solidserver

This is a plugin for the Nautobot SSoT plugin to pull selected data from EIP solidserver and merge it into Nautobot as IP Address and IP Prefix objects.

In addition to synchronizing the data, it adds the ID of the solidserver object to a nautobot custom field named solidserver addr id w/slug solidserver_addr_id and a string value.

It expects four statuses to be available - NO-IPAM-RECORD, Imported From Solidserver, Active, and Unknown.

## Installation

Build the plugin
    ```poetry build```

Install the plugin
    ```pip install nautobot-plugin-ssot-eip-solidserver```

Update nautobot_config.py
    *see configuration section*

Restart nautobot

## Constants

The constants file includes a default value for the SolidSERVER host and for the query limit size.  Override them if needed.  The host value should only get used if something has gone wrong loading the configuration.

## Configuration

The following should be added to your nautobot_config.py and updated for your environment.  Ideally, the nnn_credential object is a secret injected at runtime and not hardcoded into your config, eg environment variable in a container.

``` python
    'nautobot_ssot_eip_solidserver': {
        "nnn_user": os.getenv("NAUTOBOT_SSOT_NNN_USER",
                              "SolidServer_Nautobot_User"),
        "nnn_url": os.getenv("NAUTOBOT_SSOT_NNN_URL",
                             "https://solidserverinstance.example.com"),
        "nnn_credential": os.getenv("NAUTOBOT_SSOT_NNN_CREDENTIAL",
                                    "SUPER SECRET PASSWORD!")
    },
```

- nnn_user is expected to be a string containing a username.
- nnn_url is expected to be a string containing a url.
- nnn_credential is expected to be a string containing a password.

## Notes/tips on usage
The default timeout of 120 seconds is enough for many queries, but larger queries will take more time.  An IPv4 /18 network containing ~1700 records takes approximately 90 seconds.  An IPv4 /18 network containing ~4500 records takes approximately 270 seconds.  An IPv4 /19 network containing ~5200 records takes approxmately 300 seconds.  Exactly when to increase the timeout depends on how broad the query is and how many records are in the query results.

The name filter is sometimes useful but also can be unreliable.  If no fqdn is currently present on an address, it will not be found by the name filter and you may get job failures as the job tries to add an address that already partially exists.  CIDR filters are more reliable.

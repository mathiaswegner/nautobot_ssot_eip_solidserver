# TO DOs for nautobot plugin for SSoT with EIP Solidserver

## nautobot model

    - test nautobot side replacing solidserver_addr_id (str) with solidserver_addr_id (int)
    - revert from str to int in add/update

## nautobot adapter

    - explore using the net_host filter for getting subnet parents for IPs

## solidserver model

    - add support for pushing data back to solidserver

## solidserver adapter

    - update solidserver get cidr to use WHERE: "hostaddr >= '1.2.3.0' and hostaddr <= '1.2.3.255'"

## jobs

    - add job for pushing data back to solidserver
    - remove user/password settings from GUI

## utils

    - re-work ssutils to move solidserver client inside adapter

## housekeeping

    - make sure that all update, add, and delete actions have an info log
    - make sure that all errors have a warn or failure log
    - re-do logging in general
    - LINTING!
    - investigate speed improvements
    - increase default runtime value
    - meet with NNN team for status labeling requirements, pushing data back to solidserver requirements

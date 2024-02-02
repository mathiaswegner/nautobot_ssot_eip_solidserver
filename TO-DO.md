# TO DOs for nautobot plugin for SSoT with EIP Solidserver

## solidserver model

    - add support for pushing data back to solidserver

## nautobot model

    - override nautobot_ssot.contrib so that status is not addressed by update() methods

## jobs

    - add job for pushing data back to solidserver
    - can the name filter be made safe, or should it be removed?

## housekeeping

    - make sure that all update, add, and delete actions have an info log
    - make sure that all errors have a warn or failure log

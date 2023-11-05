# Release Notes

## 0.1.3

    - fixed bad log formatting
    - improved logging

## 0.1.2

    - fixed issue where version would report as unknown
    - switched to docker build agent instead of ec2 build agent

## 0.1.1

    - updated jenkinsfile to pull tags

## 0.1.0

    - moved username and password from job UI to env vars
    - added data mapping, config information, and object lookups to job

## 0.0.5

    - works with IP addresses in cloud instance
    - CIDR address filter works in cloud instance
    - fixed bugs preventing cloud instance from working
    - fixed bug preventing IP address deletes from succeeding

## pre-0.0.5

    - first pass at a working SSoT plugin
    - added CIDR filtering
    - added domain name filter
    - initial data models
    - initial adapters
    - job to push data from solidserver to nautobot
    - IP address sync works in laptop lab
    - prefix sync works intermittently in laptop lab

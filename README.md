Gotchas found while writing this

- global 'name' in job is REQUIRED, not optional
- SSoT plugin hides the commit checkbox by default, so set commit_default=True or override the hidden checkbox
- carrying the job object into a new object will let you log from adapters/models

# nautobot-plugin-ssot-eip-solidserver
This is a plugin for the Nautobot SSoT plugin to pull selected data from EIP solidserver and merge it into Nautobot.

### Configuration
There is no configuration in the nautobot_config.py, all options are added via the GUI when running a job.

### Installation
Add plugin to the nautobot container's requirements.txt, rebuild the container and restart the service.

### To-Dos
- explore using the net_host filter for getting subnet parents for IPs
- update solidserver get cidr to use WHERE: "hostaddr >= '1.2.3.0' and hostaddr <= '1.2.3.255'"
- re-work ssutils to move solidserver client inside adapter
- revisit logging
-

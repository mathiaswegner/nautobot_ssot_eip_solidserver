# nautobot-plugin-ssot-eip-solidserver

This is a plugin for the Nautobot SSoT plugin to pull selected data from EIP solidserver and merge it into Nautobot.

## Configuration

There is no configuration in the nautobot_config.py, all options are added via the GUI when running a job.

## Installation

Add plugin and dependencies to the nautobot container's requirements.txt, rebuild the container and restart the service.  To pin a specific version rather than using the latest, the Jenkinsfile will need to be updated to download the pinned version that matches the requirements.

## Dependencies

validators~=0.20.0

## Manually Building

```bash
export GITLAB_KEY=<gitlab token>
python3 -m build
./push_to_gitlab_registry.sh
```

## Building with Jenkins

Pending

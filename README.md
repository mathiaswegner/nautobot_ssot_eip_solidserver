Gotchas found while writing this

- global 'name' in job is REQUIRED, not optional
- SSoT plugin hides the commit checkbox by default, so set commit_default=True or override the hidden checkbox
- carrying the job object into a new object will let you log from adapters/models

# nautobot-plugin-ssot-eip-solidserver
This is a plugin for the Nautobot SSoT plugin to pull selected data from EIP solidserver and merge it into Nautobot.

### Configuration
There is no configuration in the nautobot_config.py, all options are added via the GUI when running a job.

### Installation
Add plugin and dependencies to the nautobot container's requirements.txt, rebuild the container and restart the service.

### Dependencies
validators~=0.20.0

### To-Dos
- explore using the net_host filter for getting subnet parents for IPs
- update solidserver get cidr to use WHERE: "hostaddr >= '1.2.3.0' and hostaddr <= '1.2.3.255'"
- re-work ssutils to move solidserver client inside adapter
- revisit logging
- move credentials from GUI to env (unless JOB has a different preference)

### Manually Building
cd dist
export TARFILE=`ls nautobot-plugin-ssot-eip-solidserver*.tar.gz`
echo $TARFILE
export VERSION=`echo $TARFILE | sed "s/nautobot-plugin-ssot-eip-solidserver-\([0-9]*\.[0-9]*\.[0-9]*\)\.tar\.gz/\1/"`
echo $VERSION
curl --header "PRIVATE-TOKEN: $GITLAB_KEY" \
     --user "jenkins-nautobot-ssot-eip-solidserver-plugin-key:$GITLAB_KEY" \
     --upload-file $TARFILE \
     "https://gitlab.com/api/v4/projects/upenn-isc-pine%2Fnautobot_ssot_eip_solidserver/packages/generic/nautobot-plugin-ssot-eip-solidserver/$VERSION/$TARFILE"
export LATEST_TAR=`echo $TARFILE | sed "s/-$VERSION//"`
echo $LATEST_TAR
mv "$TARFILE" "$LATEST_TAR"
curl --header "PRIVATE-TOKEN: $GITLAB_KEY" \
     --user "jenkins-nautobot-ssot-eip-solidserver-plugin-key:$GITLAB_KEY" \
     --upload-file $LATEST_TAR \
     "https://gitlab.com/api/v4/projects/upenn-isc-pine%2Fnautobot_ssot_eip_solidserver/packages/generic/nautobot-plugin-ssot-eip-solidserver/latest/$LATEST_TAR"

export WHLFILE=`ls nautobot_plugin_ssot_eip_solidserver*.whl`
echo $WHLFILE
curl --header "PRIVATE-TOKEN: $GITLAB_KEY" \
     --user "jenkins-nautobot-ssot-eip-solidserver-plugin-key:$GITLAB_KEY" \
     --upload-file $WHLFILE \
     "https://gitlab.com/api/v4/projects/upenn-isc-pine%2Fnautobot_ssot_eip_solidserver/packages/generic/nautobot-plugin-ssot-eip-solidserver/$VERSION/$WHLFILE"
export LATEST_WHL=`echo $WHLFILE | sed "s/-$VERSION//"`
echo $LATEST_WHL
mv "$WHLFILE" "$LATEST_WHL"
curl --header "PRIVATE-TOKEN: $GITLAB_KEY" \
     --user "jenkins-nautobot-ssot-eip-solidserver-plugin-key:$GITLAB_KEY" \
     --upload-file $LATEST_WHL \
     "https://gitlab.com/api/v4/projects/upenn-isc-pine%2Fnautobot_ssot_eip_solidserver/packages/generic/nautobot-plugin-ssot-eip-solidserver/latest/$LATEST_WHL"

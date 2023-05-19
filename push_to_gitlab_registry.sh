#!/bin/sh

echo "python3 -m twine upload --repository gitlab-nautobot-plugins dist/*"

exit

cd dist
if [ ! $GITLAB_KEY ]; then
  echo "No GITLAB_KEY environment variable!"
  exit 1
fi
export TARFILE=`ls nautobot-plugin-ssot-eip-solidserver*.tar.gz`
echo "Tar file is $TARFILE"
export VERSION=`echo $TARFILE | sed "s/nautobot-plugin-ssot-eip-solidserver-\([0-9]*\.[0-9a-z\+]*\.[0-9a-z\+\.]*\)\.tar\.gz/\1/"`
echo "Version is $VERSION"
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
export UPLOAD_AS=`echo $WHLFILE | sed "s/_/-/g"`
echo "Wheel file is $WHLFILE"
echo "Upload as $UPLOAD_AS"
curl --header "PRIVATE-TOKEN: $GITLAB_KEY" \
     --user "jenkins-nautobot-ssot-eip-solidserver-plugin-key:$GITLAB_KEY" \
     --upload-file $WHLFILE \
     "https://gitlab.com/api/v4/projects/upenn-isc-pine%2Fnautobot_ssot_eip_solidserver/packages/generic/nautobot-plugin-ssot-eip-solidserver/$VERSION/$UPLOAD_AS"
export LATEST_WHL=`echo $UPLOAD_AS | sed "s/-$VERSION//"`
echo $LATEST_WHL
curl --header "PRIVATE-TOKEN: $GITLAB_KEY" \
     --user "jenkins-nautobot-ssot-eip-solidserver-plugin-key:$GITLAB_KEY" \
     --upload-file $WHLFILE \
     "https://gitlab.com/api/v4/projects/upenn-isc-pine%2Fnautobot_ssot_eip_solidserver/packages/generic/nautobot-plugin-ssot-eip-solidserver/latest/$LATEST_WHL"
rm ./*
cd ..
echo

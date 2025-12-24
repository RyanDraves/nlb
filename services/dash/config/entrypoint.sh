#!/bin/sh

set -e

# Print the current user & user ID
echo "Running as user: $(whoami) with UID: $(id -u)"
# Print the permissions of the /secrets directory
echo "Permissions of /secrets directory:"
ls -ld /secrets

mkdir -p /www/assets
mkdir -p /www/assets/icons
cp /home/lighttpd/config.yaml /www/assets/config.yml
cp /home/lighttpd/favicon.ico /www/assets/icons/favicon.ico
token=$(cat /secrets/dash_portainer_token)
sed -i 's@PORTAINER_TOKEN@'"$token"'@g' /www/assets/config.yml
token=$(cat /secrets/dash_mealie_token)
sed -i 's@MEALIE_TOKEN@'"$token"'@g' /www/assets/config.yml
token=$(cat /secrets/dash_octoprint_token)
sed -i 's@OCTOPRINT_TOKEN@'"$token"'@g' /www/assets/config.yml

# Rest of entrypoint copied from https://github.com/bastienwirtz/homer

# Default assets & example configuration installation
if [[ "${INIT_ASSETS}" == "1" ]] && [[ ! -f "/www/assets/config.yml" ]]; then
    echo "No configuration found, installing default config & assets"
    if [[ -w "/www/assets/" ]];
    then
        while true; do echo n; done | cp -Ri /www/default-assets/* /www/assets/
        yes n | cp -i /www/default-assets/config.yml.dist /www/assets/config.yml
    else
        echo "Assets directory not writable, skipping default config install.";
        echo "Check assets directory permissions & docker user or skip default assets install by setting the INIT_ASSETS env var to 0."
    fi
fi

echo "Starting webserver"
exec lighttpd -D -f /lighttpd.conf

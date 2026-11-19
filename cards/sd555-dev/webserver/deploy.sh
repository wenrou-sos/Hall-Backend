#!/bin/bash

echo '[*] Git pulling...'
git pull

echo '[*] Rsync to /home/playgems_io/webserver/'
rsync -r --delete --exclude-from=excludeFiles ./ /home/playgems_io/webserver/

echo '[*] Restarting webserver service'
sudo systemctl restart webserver


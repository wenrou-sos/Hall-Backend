#!/bin/bash

echo '[*] Git pulling...'
git pull

echo '[*] Rsync to /home/playgems_io/apiserver/'
rsync -r --delete --exclude-from=excludeFiles ./ /home/playgems_io/apiserver/

echo '[*] Restarting apiserver service'
sudo systemctl restart apiserver

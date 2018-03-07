#!/bin/bash

echo "Linking config files for" $1

pyconf_path="config/config"
jsconf_path="static/js/config"

if [ ! -e $pyconf_path.$1.json ] || [ ! -e $jsconf_path.$1.js ]; then
    echo "Requested configuration is not defined"
    exit 1
fi

[ -L $pyconf_path.json ] && rm $pyconf_path.json
ln -s $pyconf_path.$1.json $pyconf_path.json
[ -L $jsconf_path.js ] && rm $jsconf_path.js
ln -s $jsconf_path.$1.json $jsconf_path.js
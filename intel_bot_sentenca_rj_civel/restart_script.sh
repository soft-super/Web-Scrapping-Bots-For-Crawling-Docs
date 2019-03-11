#!/bin/bash
# run every min, add it to cron
# * * * * * /home/ubuntu/restart_script.sh 2>> /var/test.log

ps -aux |grep 'tjrj_jus_script.py' |grep -v 'grep'

if [ $? != "0" ]; then
    grep 'finished' /home/ubuntu/intelligenti-tjrj_jus/logs/status.log
    if [ $? != "0" ]; then
        export DISPLAY=:20
        Xvfb :20 -screen 0 1366x768x16 &
        cd /home/ubuntu/intelligenti-tjrj_jus && /home/ubuntu/envname/bin/python3.6 tjrj_jus_script.py -csv_numbers dossie.dossie.csv -csv_words words.csv -store_folder ./files/ -clear_cache no
    fi
fi

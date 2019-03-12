#!/bin/bash
# run every min, add it to cron
# */30 * * * * /vagrant/intel_bot_sentenca_rs_trt_pje/cookie.sh 2> /var/test.log

/usr/bin/Xvfb :99 -ac -screen 0 1360x900x8 & export DISPLAY=":99"
# path where placed script restart_session.py
cd /vagrant/session && python restart_session.py

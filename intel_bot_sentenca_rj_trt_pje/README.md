# trt4 spider
Installation Use python2.7 or python3.6

sudo apt-get install wkhtmltopdf

pip2.7 install -r requirements.txt

python2.7 setup.py install

Install Latest Firefox Browser


### IMPORTANTLY Run one time in terminal session
```
sudo su
export DISPLAY=:20
Xvfb :20 -screen 0 1366x768x16 &
```
#### With number
parse() - return pdf text or None
```
from intel_bot_sentenca_rs_trt_pje.trt4_jus_parser import Bot

search_words = ["Sentença"]
b = Bot(load_session=True, file_name_session='/path_to_session_file/cookies_trt4.pkl')
search_words = [u"Sentença"]
b.parse('0021261-70.2015.5.04.0030', search_words)
b.driver.quit()
```

# How to configure script for bypass auth from digital server
1. On system with gui and configured CA do the next only one time:
```
from intel_bot_sentenca_rs_trt_pje.trt4_jus_parser import Bot

b = Bot(file_name_session='/path_to_session_file/cookies_trt4.pkl')
b.write_session_cookie()
b.driver.quit()
```
After that will be created file cookies_trt4.pkl

Copy this file on RPA server project_folder_path/bot
2. Configure crontab which will support session alive.
Script which will do this called:
```
intel_bot_sentenca_rs_trt_pje/cookie.sh
in line 6 replace to path where placed script:
cd /vagrant/intel_bot_sentenca_rs_trt_pje && python restart_session.py
replace /intel_bot_sentenca_sp_trt_pje with 'new_path'
crontab -e
```
add next line in cron settings:
```
*/27 * * * * /path_to_script/cookie.sh 2> /var/cookie_trt4.log
```
So after that session always will alive.

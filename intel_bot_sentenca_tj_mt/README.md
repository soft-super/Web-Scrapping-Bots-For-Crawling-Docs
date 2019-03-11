# intel_bot_sentenca_tj_mt Spider

## Installation
Use python2.7 or python3.6
```
sudo apt-get install wkhtmltopdf
pip2.7 install -r requirements.txt
python2.7 setup.py install
Install Latest Firefox Browser
```

### IMPORTANTLY Run one time in terminal session
```
sudo su
export DISPLAY=:20
Xvfb :20 -screen 0 1366x768x16 &
```
#### With number
search_process() - return pdf text
```
from intel_bot_sentenca_tj_mt.tjmt_jus_script import TjmtJusAutomation
search_words = ["sentença"]
mt = TjmtJusAutomation(headless=False)
mt.search_process(number='0000074-70.2017.8.11.0036',search_word=search_words)

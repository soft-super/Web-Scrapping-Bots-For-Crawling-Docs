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
from intel_bot_sentenca_pje_trt4_jus_br.trt4_jus_parser import Bot

search_words = ["Sentença"]
b = Bot(headless=True)
search_words = [u"Sentença"]
b.parse('0021261-70.2015.5.04.0030', search_words)
b.driver.quit()
```
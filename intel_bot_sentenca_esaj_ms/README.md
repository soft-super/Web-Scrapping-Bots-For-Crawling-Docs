
# intel_bot_sentenca_esaj_ms spider

## Installation
Use python2.7
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
```

search_process() - return pdf text

from intel_bot_sentenca_esaj_ms.tjms_jus_script import ESAJAutomation

search_words = ["Ver íntegra do(a) Sentença", "Tipo do Movimento"]
ja = ESAJAutomation(headless=False)
ja.search_process(number='2008.001.184665-8', search_word=search_words)
ja.search_process(number='0156353-61.2014.8.19.0038', search_word=search_words)
```




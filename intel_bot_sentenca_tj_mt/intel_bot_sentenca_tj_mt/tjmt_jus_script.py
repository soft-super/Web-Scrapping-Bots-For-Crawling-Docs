# -*- coding: UTF-8 -*-
# encoding=utf8  
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')
import argparse
from enum import Enum
from io import BytesIO
from time import sleep
import logging
import requests
import pdfkit
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import (
    NoSuchElementException,
    UnexpectedAlertPresentException
)
from PIL import Image

BASE_URL = 'http://www.tjmt.jus.br/'
URL_POST_CAPTCHA = 'http://2captcha.com/in.php'
URL_GET_CAPTCHA = 'http://2captcha.com/res.php'
KEY = 'c3b78102059c7d2009ea1591019068c6'
COUNT_NUMBERS = 0
CURRENT_NUMBERS = 0


logging.basicConfig(
    format='%(name)s - %(levelname)s - %(message)s'
)



class TjmtJusAutomation(object):
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = self.session()


    def session(self):
        options = webdriver.FirefoxOptions()
        if self.headless is True:
            options.add_argument('-headless')
        # PROXY = "142.93.87.88:3128"
        # options.add_argument('--proxy-server=%s' % PROXY)
        self.driver = webdriver.Firefox(
            service_log_path='/dev/null',
            options=options,
            executable_path='geckodriver')
        self.driver.set_page_load_timeout(13)
        self.driver.implicitly_wait(5)
        self.driver.set_window_size(1360, 900)

        return self.driver

    def search_process(self, number, search_word=None):
        try:
            self.driver.get(BASE_URL)
        except TimeoutException:
            logging.warning(
                '{} - Timeout in loading website'.format(
                    number
                )
            )
            return None

        try:
            self.driver.find_elements_by_xpath("//div[@class='divConsultaProcessual']"
                                                "//input[@id='processo']")[0].send_keys(number)
            self.driver.find_elements_by_xpath("//div[@class='divConsultaProcessual']"
                                               "//button[@id='buscarProcesso']")[0].click()
            sleep(1)
        except NoSuchElementException:
            logging.warning(
                '{} - Webdriver Element not found.'.format(
                    number
                )
            )
            return None
        except TimeoutException:
            logging.warning(
                '{} - Timeout in loading website'.format(
                    number
                )
            )
            return None

        try:
            captcha_pass = False
            for i in range(3):
                if self.resolve_captcha() is True:
                    captcha_pass = True
                    break
        except UnexpectedAlertPresentException:
            logging.warning(
                '{} - Download do arquivo não permitido'.format(
                    number
                )
            )

            return None

        if not captcha_pass:
            logging.warning(
                '{} - Captcha pass failed.'.format(
                    number
                )
            )
            return None

        sleep(1)

        try:
            todos_andamentos = self.driver.find_elements_by_xpath("//a[@id='phMiolo_ContentPrincipal_cphConsultaProcessoPrincipal_Principal_fvProcesso_LinkButton1']")[0]
            self.driver.get(todos_andamentos.get_attribute("href"))
        except:
            logging.warning(
                '{} - Arquivo não existe.'.format(
                    number
                )
            )
            return None

        body = self.driver.find_element_by_xpath('html/body').text
        all_files_downloaded = False
        all_trs = self.driver.find_elements_by_xpath("//div[@id='listaAndamento']/table/tbody/tr")
        for word in search_word:
            file_downloaded = False
            file_name = word + '_' + number
            previous_tr = ''
            for tr in all_trs:
                if len(tr.find_elements_by_xpath(".//td[@class='colTextFull']")) > 0:
                    if word in tr.find_elements_by_xpath(".//td[@class='colTextFull']")[0].text:
                        try:
                            webpage = previous_tr + '<br/><br/>' + tr.get_attribute('innerHTML')
                            pdf_file = self.generate_pdf(content=webpage)
                            file_downloaded = True
                            all_files_downloaded = True
                            break
                        except:
                            pass
                previous_tr = tr.get_attribute('innerHTML')
            if not file_downloaded:
                logging.warning(
                    '{} - {} - Arquivo não existe.'.format(
                        number,
                        word
                    )
                )
             
        self.driver.execute_script("window.history.go(-1)")
        sleep(2)
        if not all_files_downloaded:
            return None
   
        return True

        return pdf_file   

    def resolve_captcha(self):
        try:
            self.driver.find_element_by_id('captcha_image')
        except NoSuchElementException:
            return True

        try:
            size_image = 1360, 900
            element = self.driver.find_element_by_id('captcha_image')
            location = element.location
            size = element.size
            png = self.driver.get_screenshot_as_png()
            im = Image.open(BytesIO(png))
            im.thumbnail(size_image, Image.ANTIALIAS)
            left = location['x']
            top = location['y']
            right = location['x'] + size['width']
            bottom = location['y'] + size['height']
            im = im.crop((left, top, right, bottom))
            im.save('screenshot.png')

            files = {'file': open('screenshot.png', 'rb')}
            data = {'key': KEY}
            response = requests.post(
                URL_POST_CAPTCHA,
                files=files,
                data=data,
                timeout=15
            )
            if response.ok:
                sleep(5)
                id_message = response.text.split('|')[-1]
                resolved_captcha = requests.get(
                    '{}?key={}&action=get&id={}'.format(
                        URL_GET_CAPTCHA,
                        KEY,
                        id_message
                    ),
                    timeout=15
                )
                message = resolved_captcha.text.split('|')[-1]
                self.driver.find_element_by_id('captcha_text').send_keys(message)
                return True
        except:
            return False

    def generate_pdf(self, content):
        html = '''
            <!DOCTYPE HTML>
            <html>
                <head>
                    <meta charset="utf-8">
                </head>
                <body>
                    {content}
                </body>
            </html>
            '''.format(content=content)
        
        options = {
            'quiet': ''
        }

        pdf = HeadlessPdfKit(html, 'string', options=options).to_pdf(False)
        return pdf


class HeadlessPdfKit(pdfkit.PDFKit):
    def command(self, path=None):
        cmdlist = ['xvfb-run', '--']
        # if `auto_servernum` is in options, add the `-a` parameter which
        # should ensure that each xvfb has its own DISPLAY ID
        if 'auto_servernum' in self.options:
            cmdlist = ['xvfb-run', '-a', '--']
        return cmdlist + super(HeadlessPdfKit, self).command(path) 
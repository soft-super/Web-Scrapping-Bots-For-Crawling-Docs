# -*- coding: UTF-8 -*-
# encoding=utf8  
import sys  
reload(sys)  
sys.setdefaultencoding('utf8')

import argparse
import csv
import time
from enum import Enum
from io import BytesIO
import sys
import os
import logging

import requests
import pdfkit
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    UnexpectedAlertPresentException
)
from PIL import Image

BASE_URL = 'http://www4.tjrj.jus.br/ConsultaUnificada/' \
           'consulta.do#tabs-numero-indice0'
URL_POST_CAPTCHA = 'http://2captcha.com/in.php'
URL_GET_CAPTCHA = 'http://2captcha.com/res.php'
KEY = 'c3b78102059c7d2009ea1591019068c6'
COUNT_NUMBERS = 0
CURRENT_NUMBERS = 0

logging.basicConfig(
    format='%(name)s - %(levelname)s - %(message)s'
)


class TypeNumber(Enum):
    UNICA = 'unica'
    ANTIGA = 'antiga'
    UNKNOWN = 'unknown'


class JusAutomation(object):
    def __init__(self, headless=False):

        self.headless = headless
        self.driver = self.session()

    def session(self):
        options = webdriver.FirefoxOptions()
        if self.headless is True:
            options.add_argument('-headless')

        self.driver = webdriver.Firefox(
            service_log_path='/dev/null',
            options=options,
            executable_path='geckodriver'
        )
        self.driver.set_page_load_timeout(13)
        self.driver.implicitly_wait(5)
        self.driver.set_window_size(1360, 900)

        return self.driver

    def get_type_format_number(self, num):
        if len(num) == 25:
            return TypeNumber.UNICA
        elif len(num) == 17:
            return TypeNumber.ANTIGA

        return TypeNumber.UNKNOWN

    def search_process(self, number, search_word=None):
        self.driver.get(BASE_URL)
        type_number = self.get_type_format_number(number)

        if type_number == TypeNumber.UNICA:
            self.driver.execute_script(
                "document.getElementById('parte1ProcCNJ').value='{}'".format(
                    number[:15]))
            self.driver.find_element_by_css_selector('#form #parte2ProcCNJ'). \
                send_keys(number[21:])
            self.driver.find_element_by_name('form:commandButton3').click()

        elif type_number == TypeNumber.ANTIGA:
            self.driver.find_element_by_id(
                'selOpcaoNumeracao').find_elements_by_tag_name('label')[1]\
                .click()
            self.driver.find_element_by_name('form:btnumero').send_keys(number)
            self.driver.find_element_by_name('form:commandButton2').click()

        elif type_number == TypeNumber.UNKNOWN:
            logging.warning(
                '{} - Download do arquivo não permitido'.format(
                    number
                )
            )
            return None

        try:
            self.driver.find_element_by_id('form').find_elements_by_tag_name(
                'a')[0].click()
        except NoSuchElementException:
            pass

        except UnexpectedAlertPresentException:
            logging.warning(
                '{} - Download do arquivo não permitido'.format(
                    number
                )
            )
            return None

        for i in range(3):
            if self.resolve_captcha() is True:
                break

        try:
            self.driver.find_element_by_css_selector(
                "img[title='Listar Todos Movimentos']"
            ).click()

        except NoSuchElementException:
            pass

        all_tr_items = self.driver.find_elements_by_tag_name('tr')

        get_href_name = self.driver.find_elements_by_tag_name('a')
        search_first_word = self.driver.find_elements_by_css_selector(
            'tr.tipoMovimento'
        )

        pdf_url_name = None
        try:
            for word in search_word:
                for tr in search_first_word:
                    if word.lower() in tr.text.lower() and ' - ' in tr.text:
                        first_word = tr.text.split(':')[1].split()[0].lower()
                        for a in get_href_name:
                            if first_word.lower() in a.text.lower():
                                pdf_url_name = a.text
                                raise StopIteration
        except StopIteration:
            pass

        if pdf_url_name is None:
            return None

        description = None
        description_original = None
        if pdf_url_name is not None:
            for id, tr in enumerate(all_tr_items):
                get_all_td = tr.find_elements_by_tag_name('td')
                for td in get_all_td:
                    if pdf_url_name in td.text:
                        description = td.text.replace(
                            '(...)', '').replace('...', '').strip().replace(pdf_url_name, '')[:30]
                        description_original = td.text.replace(
                            '(...)', '').replace('...', '').strip().replace(pdf_url_name, '')
                        break

                if description:
                    break

            input_values = self.driver.find_elements_by_tag_name('input')
            search_input = ''
            for input in input_values:
                if description in input.get_attribute("value"):
                    search_input = input.get_attribute("value")
                    break

            if len(search_input) == 0:
                search = description_original.replace(' ', '').replace('\n', '')[10:30]
                for input in input_values:
                    if search in input.get_attribute("value").replace(' ', '').\
                            replace('\n', ''):
                        search_input = input.get_attribute("value")
                        break
            pdf_file = False
            if len(search_input) != 0:
                pdf_file = self.generate_pdf(search_input)

            return pdf_file

    def resolve_captcha(self):
        try:
            self.driver.find_element_by_id('imgCaptcha')

        except NoSuchElementException:
            return True

        size_image = 1360, 900
        element = self.driver.find_element_by_id('img_container')
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
        im.save('/tmp/screenshot.png')

        files = {'file': open('/tmp/screenshot.png', 'rb')}
        data = {'key': KEY}
        response = requests.post(
            URL_POST_CAPTCHA,
            files=files,
            data=data,
            timeout=15
        )
        if response.ok:
            time.sleep(15)
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
            self.driver.find_element_by_id('captcha').send_keys(message)
            self.driver.find_element_by_css_selector('input[type="button"]').\
                click()

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



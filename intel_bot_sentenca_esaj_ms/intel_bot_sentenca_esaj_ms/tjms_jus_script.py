# -*- coding: UTF-8 -*-
# encoding=utf8  

import argparse
import time
import os
import logging
import re
import random
import requests
import pyperclip
import requests.packages.urllib3
import pdfkit
from pyvirtualdisplay import Display
from enum import Enum
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import ElementNotVisibleException, TimeoutException, StaleElementReferenceException, NoSuchElementException

#https://esaj.tjms.jus.br/sajcas/login?service=https%3A%2F%2Fesaj.tjms.jus.br%2Fesaj%2Fj_spring_cas_security_check
BASE_URL = 'https://esaj.tjms.jus.br/cpopg5/open.do?gateway=true'
# URL_POST_CAPTCHA = 'http://2captcha.com/in.php'
# URL_GET_CAPTCHA = 'http://2captcha.com/res.php'
KEY = 'c3b78102059c7d2009ea1591019068c6'
SCANNED_NUMBERS_LOG = './logs/scanned_search_numbers.log'
SCANNED_STATUS = './logs/status.log'
LOGIN = '223.213.118.19'
PASSWORD = '22321311819'

logging.basicConfig(
    format='%(name)s - %(levelname)s - %(message)s'
)

class ESAJAutomation(object):
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

    def get_page(self, number):
        for _ in range(3):
            timeout = random.randint(7, 15)
            try:
                self.driver.get(BASE_URL)
                self.driver.refresh()
                time.sleep(timeout)
            except Exception:
                logging.warning(
                    '{} - Number doesnt exists or something went wrong'.format(
                        number
                    )
                )
                continue                                                                     
            break

    def get(self, timeout=10):
        try:
            self.driver.set_window_size(1366, 768)
            self.driver.get(BASE_URL)
            self.driver.refresh()
            response = requests.get(BASE_URL, verify=False, timeout=timeout)
            code = response.status_code
            if code >= 400:
                return RequestError(code)
        except Exception as e:
            pass
        return None
    
    def is_visible(self, by_type, locator, timeout=10):
        try:
            if by_type == "name":
                element = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.NAME, locator)))
            elif by_type == "selector":
                element = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, locator)))
            elif by_type == "xpath":
                element = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.XPATH, locator)))
            else:
                element = WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.ID, locator)))
            return True
        except Exception:
            return False
    
    def move_to_element(self, driver, element):
        '''
            Move the screen to element
        '''
        try:
            actions = ActionChains(driver)
            actions.move_to_element(element).perform()
        except:
            pass
    
    def get_elements_including_doc(self, elements):
        '''
            Only extract elements which include document as file
        '''
        elem_list = []

        for element in elements:
            try:
                doc_elem = element.find_element_by_class_name("linkMovVincProc")
                elem_list.append(element)
            except:
                pass
        return elem_list
    
    def search_element(self, driver, elements, search_word):
        '''
            Search sub string in text of each element.
            Return the found element
        '''
        for element in elements:
            self.move_to_element(driver, element)
            text = element.text

            for sub_string in search_word:
                if sub_string in text:
                    return element
        return None

    def search_and_download(self, driver, number, search_word):
        '''
            Search blog including sub string from payload and then try to find download link.
            Then Download it in the local directory.
        '''
        all_elements = driver.find_element_by_id("tabelaTodasMovimentacoes").find_elements_by_tag_name("tr")
        main_elements = self.get_elements_including_doc(all_elements)
        searched_result = self.search_element(driver, main_elements, search_word)

        if searched_result:
            driver.get(searched_result.find_element_by_class_name("linkMovVincProc").get_attribute("href"))
            try:
                iframe = driver.find_element_by_id("documento")
            except:
                logging.warning("{}-URL for PDF is not working!".format(number))
                return False

            result_pdf =driver.switch_to_frame(iframe)
            pdf_file = self.generate_pdf(result_pdf) #Transforma em PDF
            return pdf_file    

            # try:
            #     download_object = self.driver.find_element_by_id("download")
            #     download_object.click()
            # except:
            #     logging.warning("{}-Downloading pdf is failed".format(number))
            #     pass
            return True
        return False

    def search_process(self, number, search_word=None):
        try:
            self.driver.get(BASE_URL)
            self.driver.find_element_by_css_selector("input[id='usernameForm']").send_keys(LOGIN)
            self.driver.find_element_by_css_selector("input[id='passwordForm']").send_keys(PASSWORD)
            self.driver.find_element_by_css_selector("input[id='pbEntrar']").click()
            time.sleep(2)
            if not self.is_visible('selector', 'table.esajTabelaServico'):
                logging.warning(
                    '{} - Login information is not correct'.format(
                        number
                    )
                )
                #return None
        except Exception:
            #return None
            pass
        try:
            self.driver.get('https://esaj.tjms.jus.br/cpopg5/open.do?gateway=true')
            self.driver.refresh()
        except TimeoutException:
            pass
        try:
            if not self.is_visible('name', 'numeroDigitoAnoUnificado'):
                time.sleep(2)
                first_number_element = self.driver.find_element_by_id("numeroDigitoAnoUnificado")
                second_number_element = self.driver.find_element_by_id("foroNumeroUnificado")
                pyperclip.copy(number)
                time.sleep(1)
                first_number_element.click()
                number_element.send_keys(Keys.CONTROL + "v")
                number = number.replace("-", "").replace(".", "")
            for character in number[:13]:
                first_number_element.send_keys(character)
                time.sleep(2)    
            for character in number[-4:]:
                second_number_element.send_keys(character)
                time.sleep(2)
            search_element = self.driver.find_element_by_id("pbEnviar")

            search_element.click()
            # self.driver.find_element_by_name('numeroDigitoAnoUnificado').click().send_keys('number')


            if not self.is_visible('ID', 'linkmovimentacoes'):
                logging.warning(
                    '{} - No search result with this number'.format(
                        number
                    )
                )
                return None
            extension_element = self.driver.find_element_by_id("linkmovimentacoes")
            self.move_to_element(self.driver, extension_element)
            extension_element.click()
            self.search_and_download(self.driver, number, search_word)
        except Exception as e:
            return None


    def status_log(self, status):
        with open(SCANNED_STATUS, 'w+')as sf:
            sf.write('{status}\n'.format(status=status))

    def scanning_log_w(self, search_number):
        with open(SCANNED_NUMBERS_LOG, 'a')as sf:
            sf.write('{search_number}\n'.format(search_number=search_number))

    def scanning_log_r(self):
        if not os.path.exists(SCANNED_NUMBERS_LOG):
            return []

        with open(SCANNED_NUMBERS_LOG, 'r')as sf:
            data = sf.readlines()

        return data

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
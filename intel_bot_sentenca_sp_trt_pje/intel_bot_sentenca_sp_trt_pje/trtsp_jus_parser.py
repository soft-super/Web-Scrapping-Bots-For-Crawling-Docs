# -*- coding: UTF-8 -*-
import time
import logging
import pickle
import argparse
import csv
import time
import sys
import os
import re
import pdfkit 
import requests

from selenium import webdriver
from selenium.webdriver.support.select import Select


reload(sys)
sys.setdefaultencoding('utf8')

BASE_URL = 'https://pje.trtsp.jus.br/primeirograu/login.seam'
SEARCH_PAGE = 'https://pje.trtsp.jus.br/primeirograu/Processo/ConsultaProcessoTerceiros/listView.seam'

logging.basicConfig(
    filename='errors.log',
    filemode='w+',
    format='%(name)s - %(levelname)s - %(message)s'
)


class Bot(object):
    def __init__(
            self,
            digital_user,
            digital_password,
            digital_api_url='http://rpa-ui-prod.intelligenti.com.br/',
            headless=False,
    ):
        self.headless = headless
        self.digital_api_url = digital_api_url
        self.digital_user = digital_user
        self.digital_password = digital_password
        self.driver = self.setup_driver()

        self._login()

    def setup_driver(self):
        options = webdriver.FirefoxOptions()

        if self.headless:
            options.add_argument('-headless')

        driver = webdriver.Firefox(
            service_log_path='/dev/null',
            options=options,
            executable_path='geckodriver'
        )
        driver.set_page_load_timeout(15)
        driver.implicitly_wait(15)
        driver.set_window_size(1360, 900)

        return driver

    def is_visible_element(self, by_type, locator, timeout=10):
        try:
            if by_type == 'name':
                WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.NAME, locator)))
            elif by_type == 'id':
                WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.ID, locator)))
            elif by_type == 'selector':
                WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, locator)))
            else:
                WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.XPATH, locator)))
            return True

        except Exception:
            return False

    def _login(self):
        self.driver.get(BASE_URL)

        if self.is_visible_element('id', 'loginAplicacaoButton'):
            key = self.driver.find_element_by_id(
                id_='tokenAssinatura').get_attribute('innerHTML')

            session = requests.session()
            session.get(self.digital_api_url + 'admin/login/?next=/admin/')
            token = session.cookies['csrftoken']
            login_data = dict(
                username=self.digital_user,
                password=self.digital_password,
                csrfmiddlewaretoken=token
            )
            session.post(
                self.digital_api_url + 'admin/login/?next=/admin/',
                data=login_data
            )

            # send key on API server
            response = session.get(
                self.digital_api_url + 'digital_api/get_signed_key/?key={}'.format(
                    key)).json()

            # Fill form values of 'signature' and 'certChain'
            if response['status'] == 'ok':
                self.driver.execute_script(
                    "document.getElementById('signature').value = '{}';".format(
                        response['signature']))
                self.driver.execute_script(
                    "document.getElementById('certChain').value = '{}';".format(
                        response['certChain']))
                self.driver.execute_script('submitForm();')
                time.sleep(5)

            else:
                logging.warning('Login failed!')
                self.driver.quit()

    def get_search_page(self):
        self.driver.get(SEARCH_PAGE)

    def parse(self, number, search_words):
        self.get_search_page()

        try:
            if SEARCH_PAGE != self.driver.current_url:
                logging.warning('Error login. Please check your session.')
                return None

        except Exception:
            logging.warning('Error login. Please check your session.')
            return None

        self.driver.execute_script(
            "document.getElementById("
            "'pesquisarProcessoTerceiroForm:nrProcessoDecoration:nrProcesso'"
            ").value = arguments[0]",
            number
        )
        self.driver.find_element_by_id(
            'pesquisarProcessoTerceiroForm:searchButton'
        ).click()
        time.sleep(2)

        searched_items = self.driver.find_elements_by_css_selector('tr.rich-table-row')

        for searched_item in searched_items:
            try:
                link_text = searched_item \
                    .find_element_by_tag_name('a') \
                    .get_attribute('onclick')
                detail_page_link = re.search(
                    "'popUpDetalheProcesso', '(.*)'\);}", link_text) \
                    .group(1) \
                    .encode('utf-8')

                self.new_tab()
                self.driver.get(
                    'http://pje.trtsp.jus.br/' + \
                    detail_page_link)
                time.sleep(3)
            except:
                continue

            try:
                options = self.driver \
                .find_element_by_id(
                    'consultaProcessoDocumentoForm:comboTipoDocumentoDecoration:comboTipoDocumento') \
                .find_elements_by_tag_name(
                    'option')
                for search_word in search_words:
                    for index, option in enumerate(options):
                        if option.text.encode('ascii', 'ignore').lower() \
                                == search_word.encode('ascii', 'ignore').lower():
                            options[index].click()
                            raise StopIteration

            except StopIteration:
                break

        self.driver.find_element_by_name(
            'consultaProcessoDocumentoForm:searchButon') \
            .click()
        time.sleep(1.5)

        doc_link = ''

        try:
            tbody = self.driver.find_element_by_id('processoDocumentoGridTabList:tb')
            trs = tbody.find_elements_by_tag_name('tr')

            for tr in trs:
                doc_element = tr.find_element_by_tag_name('a')

                if (self.driver.current_url + '#') in doc_element.get_attribute('href'):
                    doc_link = 'http://pje.trtsp.jus.br' + \
                                re.search(
                                    "popUpDocumento', '(.*)'\);",
                                    doc_element.get_attribute('onclick')) \
                                .group(1) \
                                .encode('utf-8')
                else:
                    doc_link = doc_element.get_attribute('href')
                break
        except:
            return None

        if not doc_link:
            return None
        self.driver.get(doc_link)
        time.sleep(2)
        
        page_content = ''
        p = self.driver.find_elements_by_tag_name('p')

        for i in p:
            page_content += i.text + '\n'

        self.driver.close()

        try:
            pdf_file = self.generate_pdf(page_content.encode('utf-8'))
        except Exception as e:
            logging.warning('Error generate pdf file: {}'.format(e))
            return None

        return pdf_file

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

    def new_tab(self):
        """
        Opens new tab in driver
        :param driver:   Web driver
        """
        self.driver.execute_script("window.open('');")
        handles = list(self.driver.window_handles)
        self.driver.switch_to_window(handles[-1])


class HeadlessPdfKit(pdfkit.PDFKit):
    def command(self, path=None):
        cmdlist = ['xvfb-run', '--']
        # if `auto_servernum` is in options, add the `-a` parameter which
        # should ensure that each xvfb has its own DISPLAY ID
        if 'auto_servernum' in self.options:
            cmdlist = ['xvfb-run', '-a', '--']
        return cmdlist + super(HeadlessPdfKit, self).command(path)

if __name__ == '__main__':
    bot = Bot(
        digital_user='admin',
        digital_password='123098')
    search_words = [u"Sentença"]
    bot.parse('1000520-81.2016.5.02.0007', search_words)
    bot.parse('0010059-02.2015.5.01.0541', search_words)

    bot.driver.quit()

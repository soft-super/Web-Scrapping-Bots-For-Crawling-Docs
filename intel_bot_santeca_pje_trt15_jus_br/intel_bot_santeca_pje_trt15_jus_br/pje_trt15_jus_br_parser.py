# -*- coding: UTF-8 -*-
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import time
import logging
import unicodedata

from selenium import webdriver
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import pdfkit
import requests

BASE_URL = 'https://pje.trt15.jus.br/primeirograu/login.seam'
SEARCH_PAGE = 'https://pje.trt15.jus.br/primeirograu/Processo/ConsultaProcessoTerceiros/listView.seam'
DIGIGTAL_API_URL = 'http://127.0.0.1:10080/'
DIGIGTAL_USERNAME = 'admin'
DIGIGTAL_PASSWORD = '123098'

logging.basicConfig(
    filename='errors.log',
    filemode='w+',
    format='%(name)s - %(levelname)s - %(message)s'
)


class Bot(object):
    def __init__(self, headless=False):
        self.headless = headless
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
        locators = ['name', 'id']
        try:
            if by_type in locators:
                WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located((By.ID, locator)))
                return True

        except Exception:
            return False

        return False

    def _login(self):
        self.driver.get(BASE_URL)

        if self.is_visible_element('id', 'loginAplicacaoButton'):
            key = self.driver.find_element_by_id(
                id_='tokenAssinatura').get_attribute('innerHTML')

            session = requests.session()
            session.get(DIGIGTAL_API_URL + 'admin/login/?next=/admin/')
            token = session.cookies['csrftoken']
            login_data = dict(
                username=DIGIGTAL_USERNAME,
                password=DIGIGTAL_PASSWORD,
                csrfmiddlewaretoken=token
            )
            session.post(
                DIGIGTAL_API_URL + 'admin/login/?next=/admin/',
                data=login_data
            )

            # send key on API server
            response = session.get(
                DIGIGTAL_API_URL + 'digital_api/get_signed_key/?key={}'.format(
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

    def switch_to_window(self, window_id):
        self.driver.switch_to.window(self.driver.window_handles[window_id])

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
        time.sleep(5)

        try:
            self.driver.find_element_by_id(
                'consultaProcessoTerceirosList:tb'
            ).find_element_by_css_selector('tr form a').click()

        except Exception:
            logging.warning('Number was not found {}'.format(number))
            return None

        time.sleep(2)
        if len(self.driver.window_handles) == 2:
            self.switch_to_window(1)

            select_type = Select(self.driver.find_element_by_id(
                'consultaProcessoDocumentoForm:'
                'comboTipoDocumentoDecoration:comboTipoDocumento'
            ))
            try:
                for sw in search_words:
                    search_word = unicodedata.normalize('NFKD', sw).lower()

                    for index, option in enumerate(select_type.options):
                        encoded_option = unicodedata.normalize('NFKD', option.text).lower()

                        if search_word == encoded_option:
                            select_type.select_by_index(index)
                            raise StopIteration

            except StopIteration:
                pass

            self.driver.find_element_by_id(
                'consultaProcessoDocumentoForm:searchButon'
            ).click()
            time.sleep(6)

            try:
                self.driver.find_element_by_id(
                    'processoDocumentoGridTabList:tb').find_element_by_css_selector(
                    'tr').find_elements_by_css_selector('td')[5].find_element_by_tag_name('img').click()

            except Exception:
                logging.warning('Number was found {} but fail download pdf'.format(number))

            self.driver.close()
            self.switch_to_window(1)
            page_content = ''
            p = self.driver.find_elements_by_tag_name('p')

            for i in p:
                page_content += i.text + '\n'

            self.driver.close()
            self.switch_to_window(0)
            try:
                pdf_file = self.generate_pdf(page_content.encode('utf-8')
                                             )
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


class HeadlessPdfKit(pdfkit.PDFKit):
    def command(self, path=None):
        cmdlist = ['xvfb-run', '--']
        # if `auto_servernum` is in options, add the `-a` parameter which
        # should ensure that each xvfb has its own DISPLAY ID
        if 'auto_servernum' in self.options:
            cmdlist = ['xvfb-run', '-a', '--']
        return cmdlist + super(HeadlessPdfKit, self).command(path)


if __name__ == '__main__':
    b = Bot()
    search_words = [u"Sentença"]
    b.parse('0001329-25.2012.5.01.0341', search_words)
    b.parse('0010059-02.2015.5.01.0541', search_words)
    b.driver.quit()

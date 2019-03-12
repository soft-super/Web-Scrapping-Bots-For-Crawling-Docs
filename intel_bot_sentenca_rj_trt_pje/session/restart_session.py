from intel_bot_sentenca_rs_trt_pje.trt4_jus_parser import Bot
"""
Purpose this script support alive session to digital server
This script need set in crontab and set run every 30 min
"""
# file_name_session path to file cookies
b = Bot(load_session=True, file_name_session='/vagrant/session/cookies_trt4.pkl')
b.write_session_cookie()
b.driver.quit()

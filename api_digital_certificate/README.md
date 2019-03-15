# Setup API server
```
python manage migrate
python runserver 0.0.0.0:9090
```
http://127.0.0.1:9090 this address will be replacedd public ip.
# For developers part
```
import requests

# Get tokenAssinatura when you go on login page for example: https://pje.trtrj.jus.br/primeirograu/login.seam
key = self.driver.find_element_by_id(id_='tokenAssinatura').get_attribute('innerHTML')

# authenticate on API server
api_login_url = 'http://127.0.0.1:9090/admin/login/?next=/admin/'
session = requests.session()
session.get(api_login_url)
token = session.cookies['csrftoken']
login_data = dict(
    username='admin',
    password='123098',
    csrfmiddlewaretoken=token
)
session.post(api_login_url, data=login_data)

# send key on API server
response = session.get('http://127.0.0.1:9090/digital_api/get_signed_key/?key={}'.format(key)).json()

# Fill form values of 'signature' and 'certChain'
if response['status'] == 'ok':
    self.driver.execute_script(
        "document.getElementById('signature').value = '{}';".format(response['signature']))
    self.driver.execute_script(
        "document.getElementById('certChain').value = '{}';".format(response['certChain']))
    self.driver.execute_script('submitForm();')
```

Success API response:
```
{
"signature": "IVi/fzG9WSE+xOOtVHfnM2Cx8fxk1sH139UfcW3KGLQUhzOFjHnYhsj5Hl/3ZWwFafC2Qf12hBSvgPWUVE2rMtteo7iQ5TNCJ6uXPwCtlmejRYPdq2VrFQ==",
"certChain": "MIIcGDCCBqEwggSJoAMCAQICAQEwDQYJKoZIhvcNAQENBQAwgZcxCzAJBgNVBAYTAkJSMRMwEQYDVQQKDApJQ1AtQnJhc2lDLio=",
"certChainStringLog": "",
"status": "ok"
}
```
Bad API response:
```
{"status": "fail"}
```

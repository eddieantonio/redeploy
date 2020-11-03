import json
import os
import subprocess
import sys
from ipaddress import IPv4Address, IPv6Address
from json import JSONDecodeError
from pathlib import Path
from typing import Union, Optional

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

EXAMPLE_SECRET = "n23inimQh5ROuhRvZr2vchGOhfe_EcZQEZcOJplVP_w"



@pytest.fixture(scope="session", autouse=True)
def ensure_test_whitelist_ip():
    """
    Create ip-whitelist.json if it doesn't exist.
    Ensure test whitelist IP and test app {"example": ["111.11.111.111"]}  is in ip-whitelist.json
    """
    ip_whitelist_path = PROJECT_ROOT / 'redeploy' / 'ip-whitelist.json'

    ip_whitelist = {"example": ["111.11.111.111"]}
    if ip_whitelist_path.exists():
        with open(ip_whitelist_path) as f:
            try:
                ip_whitelist = json.load(f)
                ip_whitelist["example"] = ["111.11.111.111"]
            except JSONDecodeError:
                pass

    with open(ip_whitelist_path, 'w') as f:
        json.dump(ip_whitelist, f)


# apache gives cgi script env vars and data (in stdin)
# a typical set of env vars cgi script receives, when there IS -dsecret=xxxxxxx:
"""
{'HTTP_HOST': 'sapir.artsrn.ualberta.ca', 'HTTP_USER_AGENT': 'curl/7.47.0', 'HTTP_ACCEPT': '*/*',
 'CONTENT_LENGTH': '50', 'CONTENT_TYPE': 'application/x-www-form-urlencoded', 
'SERVER_SIGNATURE': '<address>Apache/2.4.18 (Ubuntu) Server at sapir.artsrn.ualberta.ca Port 80</address>\n',
 'SERVER_SOFTWARE': 'Apache/2.4.18 (Ubuntu)', 'SERVER_NAME': 'sapir.artsrn.ualberta.ca', 'SERVER_ADDR': '142.244.64.99',
  'SERVER_PORT': '80', 'REMOTE_ADDR': '142.244.64.99', 'DOCUMENT_ROOT': '/var/www', 'REQUEST_SCHEME': 'http',
   'CONTEXT_PREFIX': '/redeploy/', 'CONTEXT_DOCUMENT_ROOT': '/opt/redeploy/redeploy/',
    'SERVER_ADMIN': 'webmaster@localhost', 'SCRIPT_FILENAME': '/opt/redeploy/redeploy/cree-dictionary',
     'REMOTE_PORT': '53006', 'GATEWAY_INTERFACE': 'CGI/1.1', 'SERVER_PROTOCOL': 'HTTP/1.1', 'REQUEST_METHOD': 'POST',
      'QUERY_STRING': '', 'REQUEST_URI': '/redeploy/cree-dictionary', 'SCRIPT_NAME': '/redeploy/cree-dictionary'}
"""

# a typical set of env vars cgi script receives, when there is NO -dsecret=xxxxxxx:
# notice the lack of CONTENT_LENGTH and CONTENT_TYPE
"""
{'HTTP_HOST': 'sapir.artsrn.ualberta.ca', 'HTTP_USER_AGENT': 'curl/7.47.0', 'HTTP_ACCEPT': '*/*', 
, 'SERVER_SIGNATURE': '<address>Apache/2.4.18 (Ubuntu) Server at sapir.artsrn.ualberta.ca Port 80</address>\n',
 'SERVER_SOFTWARE': 'Apache/2.4.18 (Ubuntu)', 'SERVER_NAME': 'sapir.artsrn.ualberta.ca', 
 'SERVER_ADDR': '142.244.64.99', 'SERVER_PORT': '80', 'REMOTE_ADDR': '142.244.64.99',
  'DOCUMENT_ROOT': '/var/www', 'REQUEST_SCHEME': 'http', 'CONTEXT_PREFIX': '/redeploy/',
   'CONTEXT_DOCUMENT_ROOT': '/opt/redeploy/redeploy/', 'SERVER_ADMIN': 'webmaster@localhost',
    'SCRIPT_FILENAME': '/opt/redeploy/redeploy/cree-dictionary',
     'REMOTE_PORT': '54550', 'GATEWAY_INTERFACE': 'CGI/1.1', 'SERVER_PROTOCOL': 'HTTP/1.1', 'REQUEST_METHOD': 'POST', 
     'QUERY_STRING': '', 'REQUEST_URI': '/redeploy/cree-dictionary', 'SCRIPT_NAME': '/redeploy/cree-dictionary'
"""

# typical data (fed in stdin):
"secret=xN3dM-YoFZmnF1TxDKUuENy-VAcMZTaflsPHypM-EP1"


def mock_cgi_request(app_name: str, ip: Union[IPv4Address, IPv6Address], secret: Optional[str] = None, method="POST"):
    """
    :param app_name: name of the app under redeploy/
    :param ip: can be constructed like ipaddress.ip_address("127.0.0.1")
    :param secret: secret data, to be compared against  <app>.key. Can be omitted when IP is whitelisted
    :param method: "POST" | "GET" | etc.
    :raises CalledProcessError: if redeploy/<app> exits with non zero code
    """



    env = dict(os.environ)
    env.update({"REQUEST_METHOD": method, "REMOTE_ADDR": str(ip)})

    data = ""
    if secret:
        data = f"secret={secret}"
        content_length = len(data)
        env.update({"CONTENT_LENGTH": str(content_length),
                "CONTENT_TYPE": "application/x-www-form-urlencoded"})


    subprocess.run([sys.executable, str(PROJECT_ROOT / 'redeploy' / app_name)], input=data.encode('utf-8'), check=True,
                   env=env)

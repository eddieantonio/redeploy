import os
import subprocess
import sys
from ipaddress import IPv4Address, IPv6Address
from pathlib import Path
from typing import Union, Optional

PROJECT_ROOT = Path(__file__).parent.parent

EXAMPLE_SECRET = "n23inimQh5ROuhRvZr2vchGOhfe_EcZQEZcOJplVP_w"

# @pytest.fixture(autouse=True, scope="session")
# def temp_noop_redeployment():
#     """
#     create a temporary redeployment file redeploy/noop that runs noop operation `$ true`
#     associated secret key is also generated, if this test is run on Unix key will have current owner and group
#     This fixture will be automatically used so that the noop redeployment file is available during the entire test session.
#     """
#     noop_file = (PROJECT_ROOT / "redeploy" / "example")
#     key_file = PROJECT_ROOT / "noop.key"
#     key_file.write_text(NOOP_SECRET)


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


def mock_cgi_request(app_name: str, ip: Union[IPv4Address, IPv6Address], secret: Optional[str] = None, method="POST",
                     v: Optional[int] = None, file: Optional[str] = None):
    """
    :param v: If given, it corresponds to -dv= in curl
    :param file: If given, it corresponds to --data-binary @file_path in curl
    :param app_name: name of the app under redeploy/
    :param ip: can be constructed like ipaddress.ip_address("127.0.0.1")
    :param secret: secret data, to be compared against  <app>.key. Can be omitted when IP is whitelisted. If given,
        it correspondes to -dsecret= in curl
    :param method: "POST" | "GET" | etc.
    :raises CalledProcessError: if redeploy/<app> exits with non zero code
    """

    env = dict(os.environ)
    env.update({"REQUEST_METHOD": method, "REMOTE_ADDR": str(ip)})


    data = ""

    if secret:
        data += f"secret={secret}"
    if v:
        data += f"&v={v}"
    if file:
        data += f"&{file}"

    if data:
        content_length = len(data)
        env.update({"CONTENT_LENGTH": str(content_length),
                        "CONTENT_TYPE": "application/x-www-form-urlencoded"})

    subprocess.run([sys.executable, str(PROJECT_ROOT / 'redeploy' / app_name)], input=data.encode('utf-8'), check=True,
                   env=env)

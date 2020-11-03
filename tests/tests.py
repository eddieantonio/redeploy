from ipaddress import ip_address

from .conftest import mock_cgi_request, EXAMPLE_SECRET

# google.com's ip
EVIL_IP = ip_address('209.85.231.104')

# made up
WHITELISTED_IP = ip_address('111.11.111.111')


def test_invalid_key(capfd):
    mock_cgi_request("example", EVIL_IP, secret="123")
    # status 400: bad request
    assert "400" in capfd.readouterr()[0]


def test_valid_key(capfd):
    mock_cgi_request("example", EVIL_IP, secret=EXAMPLE_SECRET)
    # status 200
    assert "200" in capfd.readouterr()[0]


def test_whitelisted_ip_no_key(capfd):
    mock_cgi_request("example", WHITELISTED_IP)
    # status 200
    assert "200" in capfd.readouterr()[0]


def test_whitelisted_ip_with_key(capfd):
    mock_cgi_request("example", WHITELISTED_IP, secret=EXAMPLE_SECRET)
    # status 200
    assert "200" in capfd.readouterr()[0]

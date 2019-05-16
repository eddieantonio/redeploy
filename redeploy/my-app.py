#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import cgitb
import os
import subprocess
from pathlib import Path

DIRECTORY = '/Users/eddieantonio/Projects/itwewina/neahtta'
SCRIPT = 'git pull && touch itwewina.wsgi'


class RedeployError(Exception):
    """
    Base class for all exceptions in this module.
    """


class InadequatePermissionsError(RedeployError):
    """
    Raised when the permissions to something is wrong.
    """

class InvalidKeyError(RedeployError):
    """
    Raised when no key, or an invalid key was given.
    """


class InvalidHTTPInvocationError(RedeployError):
    """
    Raised when we are invoked using the wrong request method.
    """


def cgimain():
    redeploy()
    print("Content-Type: text/plain")
    print()


def redeploy():
    # Enable CGI tracebacks, for debugging.
    cgitb.enable()

    here = Path(__file__).parent
    app = Path(__file__).stem
    secret_key_file = here / app.with_suffix('.key')

    # Figure out if we should respond at all.
    if os.getenv('REQUEST_METHOD', 'GET').upper() != 'POST':
        raise InvalidHTTPInvocationError

    # Open the secret.
    secret = secret_key_file.read_text()

    # Figure out if we have the right permissions.
    # Note that the secret key file should ONLY be visible to this very
    # process!
    my_user = os.getuid()
    my_group = os.getgid()

    # So techically, there's a race codition here (permissions could have
    # changed between time open() and the following call to stat()), but I
    # don't mind it too much.
    stat = secret_key_file.stat()
    if stat.st_uid != my_user:
        raise InadequatePermissionsError('invalid owner for secret key')
    if stat.st_gid != my_group:
        raise InadequatePermissionsError('invalid owner for secret key')
    if stat.st_mode != 0o600:
        raise InadequatePermissionsError(
            'invalid permissions for secret key. \n'
            'chmod 600 <my-key-file>'
        )

    if key != secret:
        raise InvalidKeyError

    # We can do it!
    with Path(DIRECTORY):
        subprocess.run(SCRIPT, shell=True)

if __name__ == '__main__':
    cgimain()

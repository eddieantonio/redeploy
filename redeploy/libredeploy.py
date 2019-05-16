#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

"""
A CGI script for redeploying applications.

Usage:

    from libredeploy import redeploy
    redeploy(app_name=__file__,
             directory='/path/to/the/app',
             script='this is a shell script')
"""

import cgi
import os
import secrets
import subprocess
import stat
from contextlib import contextmanager
from pathlib import Path



################################# Exceptions #################################

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


def redeploy(*args, **kwargs):
    """
    Redeploy the web application.

    Intended to be run as a CGI script.
    """
    print("Content-Type: text/plain")
    print()
    _redeploy(*args, **kwargs)


def _redeploy(app_name, directory, script):
    """
    How to use:


    """
    app = Path(app_name)
    secret_key_file = app.with_suffix('.key')

    # Figure out if we should respond at all.
    if os.getenv('REQUEST_METHOD', 'GET').upper() != 'POST':
        raise InvalidHTTPInvocationError('Request should use POST method')

    try:
        given_secret = cgi.parse()['secret'][0]
    except (KeyError, IndexError):
        raise InvalidHTTPInvocationError('Key not provided')


    # Open the secret.
    try:
        local_secret = secret_key_file.read_text()
    except FileNotFoundError:
        raise InvalidKeyError("You forgot to generate a secret key.")


    # Figure out if we have the right permissions.
    # Note that the secret key file should ONLY be visible to this very
    # process!
    my_user = os.getuid()
    my_group = os.getgid()

    # So techically, there's a race codition here (permissions could have
    # changed between time open() and the following call to stat()), but I
    # don't mind it too much.
    key_stat = secret_key_file.stat()
    if key_stat.st_uid != my_user:
        raise InadequatePermissionsError('invalid owner for secret key')
    if key_stat.st_gid != my_group:
        raise InadequatePermissionsError('invalid owner for secret key')
    if stat.filemode(key_stat.st_mode) not in ('-r--------', '-rw-------'):
        print(stat.filemode(key_stat.st_mode))
        raise InadequatePermissionsError(
            'invalid permissions for secret key.\n'
            'chmod 600 <my-key-file>'
        )

    if not secrets.compare_digest(local_secret, given_secret):
        raise InvalidKeyError

    # We can do it!
    with cd(directory):
        subprocess.run(script, shell=True, check=True)


@contextmanager
def cd(path):
    """
    Changes the current working directory, then changes back.

    Usage:

    with cd('some-directory'):
        do_stuff()
    # Now you're back in the original directory!
    """
    old_path = os.getcwd()
    yield os.chdir(path)
    os.chdir(old_path)


if __name__ == '__main__':
    cgimain()

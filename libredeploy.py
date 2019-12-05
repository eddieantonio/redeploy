#!/usr/bin/env python3.6
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
from sys import stderr


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


################################## Main API ##################################


def redeploy(*args, **kwargs):
    """
    Redeploy the web application.

    Intended to be run as a CGI script.
    """
    try:
        _redeploy(*args, **kwargs)
    except InvalidHTTPInvocationError:
        uri = os.getenv("SERVER_NAME") + os.getenv("SCRIPT_NAME")
        print("Status: 405 Method Not Allowed")
        print("Content-Type: text/plain\r\n\r\n")

        print("Status: 405 Method Not Allowed")
        print(
            "Invalid invocation. "
            "You must make a POST request with the secret.\n"
            "\n"
            "    curl -XPOST -dsecret=XXXXXX " + uri
        )
    except RedeployError as err:
        print("Status: 400 Bad Request")
        print("Content-Type: text/plain\r\n\r\n")

        print("Status: 400 Bad Request")
        print("Could not redeploy:", type(err).__name__)
    except subprocess.CalledProcessError as err:
        print("Status: 500 Server Error")
        print("Content-Type: text/plain\r\n\r\n")

        print("Status: 500 Server Error")
    else:
        # All went okay :)
        print("Status: 200 OK")
        print("Content-Type: text/plain\r\n\r\n")

        print("Redeployment script run.")


def _redeploy(app_name, directory, script, env=None):
    if env is None:
        env = {}

    # Read the secrets!
    given_secret = get_requested_secret()
    # Only load our secret after we've verified we could get theirs.
    local_secret = get_local_secret(app_name)

    # Did the request provide the right secret?
    if not secrets.compare_digest(local_secret, given_secret):
        raise InvalidKeyError

    # Secret verified! Run the redeploy script!

    # Setup the environment
    new_env = os.environ.copy()
    new_env.update(env)

    with cd(directory):
        subprocess.run(script, shell=True, check=True, stdout=subprocess.DEVNULL)


def get_local_secret(app_name: str):
    """
    Gets the secret relative to the app path. The secret should be kept in a
    file with chmod 600 or chmod 400 mode -- only allow reads from owner and
    NOBODY else!
    """

    secret_key_file = Path(Path(app_name).parents[1], Path(app_name).stem).with_suffix(
        ".key"
    )

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
        raise InadequatePermissionsError("invalid owner for secret key")
    if key_stat.st_gid != my_group:
        raise InadequatePermissionsError("invalid owner for secret key")
    if stat.filemode(key_stat.st_mode) not in ("-r--------", "-rw-------"):
        raise InadequatePermissionsError(
            "invalid permissions for secret key.\n" "chmod 600 <my-key-file>"
        )

    return local_secret


def get_requested_secret():
    # Figure out if we should respond at all.
    if os.getenv("REQUEST_METHOD", "GET").upper() != "POST":
        raise InvalidHTTPInvocationError("Request should use POST method")

    # What is the secret?
    try:
        return cgi.parse()["secret"][0]
    except (KeyError, IndexError):
        raise InvalidHTTPInvocationError("Key not provided")


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


if __name__ == "__main__":
    redeploy()

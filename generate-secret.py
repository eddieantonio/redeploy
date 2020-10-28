#!/usr/bin/env python3.6
# -*- coding: UTF-8 -*-

"""
Usage:

    generate-secret.py <app-name>

Generates a secret key called <app-name>.key.
"""

import sys
import secrets
from pathlib import Path
import shutil
import logging

logger = logging.getLogger(__name__)

app_name = Path("redeploy", sys.argv[1])
assert app_name.exists()
key_file = Path(sys.argv[1]).with_suffix(".key")
key_file.write_text(secrets.token_urlsafe())

try:
    shutil.chown(key_file, user="www-data", group="www-data")
except LookupError as e:
    # docs.python.org says shutil.chown is only available to Unix as of python 3.6
    # when it's tried on Windows, it always throws LookupError with message "no such user: 'xxx' "
    # even if xxx is a legitimate user on Windows

    # todo: figure out what's necessary on Windows.
    #   However since redeploy is very possibly to be used on Linux servers, this hardly matters.
    logger.error(e)
    logger.error("Failed to change the owner of key file to www-data."
                 "Key file is created anyways.")

key_file.chmod(0o400)

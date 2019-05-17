#!/usr/bin/env python3
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

app_name = Path("redeploy", sys.argv[1])
assert app_name.exists()
key_file = Path(sys.argv[1]).with_suffix(".key")
key_file.write_text(secrets.token_urlsafe())

shutil.chown(key_file, user="www-data", group="www-data")
key_file.chmod(0o400)

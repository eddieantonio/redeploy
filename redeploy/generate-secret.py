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

app_name = Path(sys.argv[1])
assert app_name.exists()
key_file = app_name.with_suffix('.key')
key_file.write_text(secrets.token_urlsafe())
key_file.chmod(0o400)

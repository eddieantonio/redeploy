redeploy
========

Enables web application redeployment via HTTPS.

Usage
-----

    $ curl -XPOST -dsecret={key} https://sapir.artsrn.ualberta.ca/redeploy/{app}

Examples:

    $ curl -XPOST -dsecret=hunter2 https://sapir.artrsn.ualberta.ca/redeploy/cree-dictionary
    $ curl -XPOST -dsecret=password123 https://sapir.artrsn.ualberta.ca/redeploy/itwewina
    $ curl -XPOST -dsecret='asdfjkl;' https://sapir.artrsn.ualberta.ca/redeploy/validation

Why?
----

`sapir.artsrn.ualberta.ca`'s firewall settings let external IP addresses
to only be able to access HTTP and HTTPS ports. You **cannot SSH into
Sapir outside of the University of Alberta network**.

However, it is still desirable to redeploy applications from outside of
the University of Alberta premises (or its VPN).

The solution is `redeploy`.

For example, this enables **continuous delivery** via Travis-CI. The
Travis-CI servers somehow need to be able to notify Sapir that it's okay
to pull the latest changes from the production branch and reload the
application. Thus, Travis-CI is configured, after build success, to
issue the following HTTP request:

    POST https://sapir.artrsn.ualberta.ca/redeploy/cree-dictionary

The secret key is... well, a secret!

Travis-CI supports [encryption keys](https://docs.travis-ci.com/user/encryption-keys/).
Encrypt a value, and issue the appropriate HTTP request with curl.
Thus, Travis can now redeploy applications as soon as the production
branch is updated!

Setting up a new application for deployment
-------------------------------------------

To enable a new application for redeployment:

 1. Create a CGI script in `redeploy/{app}`
 2. Create a secret key using `python3.6 ./redeploy/generate-secret.py {app}`
 3. Ensure all of the permissions are correct!
 4. [Optional] Enable continuous deployment on Travis-CI.


### Creating a CGI script

Use the following template to create a CGI script called `redeploy/{app}`:

```python
#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

from libredeploy import redeploy

redeploy(app_name=__file__,
         directory='/path/to/your/application',
         script='git pull && ./reload')
```


Change `directory` to the directory in which your application resides.
Change `script` to a shell command that redeploys your application. This
typically begins with a `git pull`, and executes a command to reload
your application somehow. The reloading command depends on the
application and its configuration.

For example, if my app is called `flabbergaster`, I'll save this as
`redeploy/flabbergaster`.

Next is to make sure the server can execute this file. Set its
permissions to allow for execution:

    chmod +x redeploy/flabbergaster

### Creating a secret key

Use the `redeploy/generate-secret.py` script to generate a secret key.

    redeploy/generate-secret.py redeploy/{app}

This will set permissions for the secret key as appropriate. Note: **only
the owner of the file has read permissions!**

### Ensure all the permissions are correct

TBD. :/


### Enable continuous deployment on Travis-CI

TODO:

    travis encrypt DEPLOY_KEY="this is the secret key" --add

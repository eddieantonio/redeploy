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

 1. Create a CGI script as `redeploy/redeploy/{app}`. The script is written in python3 but without a suffix. 
 The easiest way is to `$ cp example {app}` with the `example` file in that directory and edit as needed.
 2. Create a secret key using `python3.6 ./redeploy/generate-secret.py {app}`
 3. Ensure all of the permissions are correct! `example` script has status `www-data:www-data` with mode `a+x` (executable for all). The generated `secret.key` has status `www-data:www-data` with mode `400`. The permissions should work with default apache configurations.
 4. [Optional] Enable continuous deployment on Travis-CI.


### Creating a CGI script

Under `redeploy/redeploy/` `$ cp example {app}` to create a template similar to the following:

```python
#!/usr/bin/env python3.6
# -*- coding: UTF-8 -*-

from libredeploy import redeploy

redeploy(app_name=__file__,
         directory='/path/to/your/application',
         script='git pull && ./reload')
```
For a Django project, an example like the following should work:
```python
script="git pull && python mysite/manage.py collectstatic --clear --no-input && touch mysite/mysite/wsgi.py"
```
where touching wsgi.py restarts the service


Change `directory` to the directory in which your application resides.
Change `script` to a shell command that redeploys your application. This
typically begins with a `git pull`, and executes a command to reload
your application somehow. The reloading command depends on the
application and its configuration.

For example, if my app is called `flabbergaster`, I'll save this as
`redeploy/redeploy/flabbergaster`.

The file should be already executable if you copy from `example` template. If not, make sure the server can execute 
this file. Set its permissions to allow for execution:

    sudo chmod +x flabbergaster
    


### Creating a secret key

Use the `./generate-secret.py` script to generate a secret key.

    generate-secret.py {app}

This will set permissions for the secret key as appropriate. Note: **only
the owner of the file has read permissions!**

### Ensure all the permissions are correct

The redeployment script is executed by apache as user `www-data`. To give apache permission to edit your project files. 
Set the owner of your project files to `www-data`. For example:

```bash
sudo chown -R www-data:www-data /opt/flabbergaster
```    


### Enable continuous deployment on Travis-CI

 1. `cd` into your project directory on sapir. For example `$ cd /opt/flabbergaster`
 2. Login on travis `$ travis login --org`
 3. Encrypt the key file of your application with `$ sudo travis encrypt-file /opt/redeploy/{app}.key --add` . 
 This will generate a `{app}.key.enc` in your current directory, as well as add a `before install` key in `.travis.yml` so
 that while travis is testing your app, the `.key.enc` file is reversed to `.key` file.
 4. Write the `.travis.yml` file in multiple staged fashion with an extra `deploy` stage. The following is a template 
 which runs two parallel jobs in the test stage and runs deployment stage after that. Note that stages runs in order and
 deployment stage won't execute if either one of the test jobs in the first stage fails. Also remove line `if: branch = master`
 if you want branches other than master that pass tests to get deployed.
 5. Don't forget to `git push` after this.
 
 ```yml
 
dist: xenial
 
stages:
  - test
  - name: deploy
    if: branch = master # don't run deploy stage if branch is not master

jobs:
  include:
  
    # job No.1. Job defaults to test stage if not specified
    - language: python
      python:
          - "3.7"
      cache: pip

      install:
          - pip install -r requirements.txt

      script:
          - coverage run --source CreeDictionary/ CreeDictionary/manage.py test API
          - coverage report -m

    # job No.2 Job defaults to test stage if not specified
    - language: node_js
      node_js:
          - "10"
      cache:
          npm: true
          directories:
          - ~/.cache
      install:
          - sudo apt-get -y install python3-pip python3-setuptools python-dev xvfb libgtk2.0-0 libnotify-dev libgconf-2-4 libnss3 libxss1 libasound2 apache2-dev
          - sudo -H pip3 install -r requirements.txt
          - npm ci
      script:
          - npm run build
          - npm run django3:migrate
          - npm run django3 & $(npm bin)/wait-on http-get://127.0.0.1:8000
          - $(npm bin)/cypress run --project ./CreeDictionary/React/cypressTest

 
    - stage: deploy
    
      # job No.3. Job belongs to deploy stage as specified
      install: sudo apt-get -y install curl
      script: curl -XPOST -dsecret=$(sudo cat cree-dictionary.key) sapir.artsrn.ualberta.ca/redeploy/cree-dictionary
 
 
 # script automatically added by "travis encript-file". Move this to deploy stage above if you don't want 
 # other jobs to be affected.
 
 before_install:
- openssl aes-256-cbc -K $encrypted_49b37942e026_key -iv $encrypted_49b37942e026_iv
  -in cree-dictionary.key.enc -out /opt/redeploy/cree-dictionary.key -d
 ```


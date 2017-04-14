#!/usr/bin/env python
#
# Copyright 2014 Major Hayden
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import urlparse
import urllib3
import socket
import json
import time
import uuid
import os


from simplegist import Simplegist
from flask      import Flask, Response, request, send_from_directory, jsonify, redirect, abort

from shorten import UrlShortener 

urllib3.disable_warnings()


GIST_FILE_HEADER     = os.environ['GIST_FILE_HEADER']
GIST_TMPDIR           = os.environ['GIST_TMPDIR']
GIST_FILENAME_HEADER = os.environ['GIST_FILENAME_HEADR']
GIST_DESC_HEADER     = os.environ['GIST_DESC_HEADER']
GIST_USER            = os.environ['GIST_USER']
GIST_TOKEN           = os.environ['GIST_TOKEN']
REALIP_HDR           = os.environ['REALIP_HDR']
USER                 = os.environ['USER']
GROUP                = os.environ['GROUP']

app    = Flask(__name__, static_folder='static')
linksh = UrlShortener()

@app.route('/link_get/<code>')
def expand_url(code):
    url = linksh.lookup(code)

    if not url:
        abort(404)

    return redirect(url)


@app.route('/link_set', methods=['POST'])
def shorten_url():
    if not request.json or 'longUrl' not in request.json:
        print('NOOOO\n')
        abort(404)

    long_url = urlparse.urlparse(request.json['longUrl'])

    if long_url.netloc == '':
        url = 'http://' + request.json['longUrl']
    else:
        url = request.json['longUrl']

    res = linksh.shorten(url)

    print ("shortened %s to %s", url, res)

    return jsonify(res)


@app.route('/_gist',  methods=['POST'])
def gist_it():
    if request.method != 'POST':
        abort(404)

    # where nginx stores the client body files.
    file_name = request.headers.get(GIST_FILE_HEADER)

    if not file_name or os.path.dirname(file_name) != GIST_TMPDIR:
        abort(404)


    try:
        filename = request.headers.get(GIST_FILENAME_HEADER)
    except:
        filename = 'cfgsh'

    try:
        descrip = request.headers.get(GIST_DESC_HEADER)
    except:
        descrip = 'nop' 

    gist = Simplegist(username=GIST_USER,
                      api_token=GIST_TOKEN)


    with open(file_name, 'r') as fp:
        _content = fp.read()

    # description name public content
    response = gist.create(name        = str(filename),
                           description = str(descrip),
                           public      = False,
                           content     = _content)

    return jsonify(response)


@app.route('/uu',  methods=['GET'])
def gen_uuid():
    return jsonify(str(uuid.uuid4()))

@app.route('/rng', methods=['GET'])
def gen_randoms():

    rando = list()

    for i in range(0, 4):
        rando.append(uuid.uuid4().int & (1<<64)-1)

    return jsonify(rando)


@app.route("/hdr", methods=['GET'])
def headers():
    hdrs = dict(request.headers)

    # remove the header set by nginx before
    # dumping
    hdrs.pop(REALIP_HDR, None)

    return jsonify(hdrs)

@app.route("/ip", methods=['GET'])
def ip():
    rip = str()

    # chrome-type data savers. The save-data is set if
    # on, and the real ip address can be found at Forwarded: for=[]
    if request.headers.get("Save-Data") and request.headers.get("Forwarded"):
        try:
            rip = request.headers.get('Forwarded', None).strip('for=\"[')[:-1]
        except:
            abort(404)
    else:
        rip = request.headers.get(REALIP_HDR)

    if not rip:
        rip = request.remote_addr

    return jsonify(rip)

@app.route("/epoch", methods=['GET'])
def epoch():
    return jsonify(int(time.time()))


@app.route('/help', methods=['GET'])
def help(): 
   
    helpers = [
        { 'Fetch your current IP address' : 'http://ip.cfg.sh'   },
        { 'Fetch the current EPOCH'       : 'http://time.cfg.sh' },
        { 'Display browser headers'       : 'http://hdr.cfg.sh'  },
        { 'Generate 4 random numbers'     : 'http://rng.cfg.sh'  },
        { 'Quickly create a gist'         : 'http://gst.cfg.sh'  },
        { 'This help :)'                  : 'http://help.cfg.sh' }
    ]

    return jsonify(helpers)


@app.route("/", methods=['GET'])
def icanhazroot():
    abort(404)


if __name__ == "__main__":
    import pwd
    import grp

    os.setegid(grp.getgrnam(USER)[2])
    os.seteuid(pwd.getpwnam(GROUP)[2]);
    app.run()

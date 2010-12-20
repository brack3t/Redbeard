"""
TODO
"""
__author__ = 'Chris Jones, Kenneth Love'
__version__ = '0.8.1'
__license__ = 'MIT'

import re

from flask import Flask, render_template, redirect, url_for, request, flash
from flask import session, jsonify

from flaskext.wtf import Form, TextField, Required

import redis
from redis.exceptions import ConnectionError, ResponseError

import settings

SECRET_KEY = '781b0650af13493089a6ffafac755a61'

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True

# Forms
class StringForm(Form):
    key_name = TextField('Key', validators=[Required()])
    key_value = TextField('Value', validators=[Required()])

@app.context_processor
def get_db_size():
    r = get_redis_connection(session)
    if not r:
        return {'db_size':0}

    return dict(db_size=r.dbsize())

@app.route('/new', methods=['GET', 'POST'])
def new_key():
    form = StringForm(request.form or None)
    if form.validate_on_submit():
        key = request.form['key_name']
        value = request.form['key_value']

        r = get_redis_connection(session)
        if not r:
            return redirect(url_for('setup'))

        if r.exists(key):
            return jsonify(flash=key + ' already exists.')

        try:
            r.set(key, value)
            flash('%s was saved successfully.' % key)
            return redirect('#%s' % key)
        except:
            return jsonify(flash=key + ' was not saved successfully.')

    return render_template('new_key.html', form=form)

def get_redis_connection(session):
    """
    Get Redis connection with session values. Ping Redis
    to make sure connection is working.
    """
    r = redis.Redis(
        host=session.get('redis_host', settings.REDIS_HOST),
        port=session.get('redis_port', settings.REDIS_PORT),
        db=session.get('redis_db', settings.REDIS_DB),
        password=session.get('redis_password', ''))

    try:
        r.ping()
    except (ConnectionError, ResponseError):
        return None

    return r

def set_session_defaults(session):
    """ Setup default session """
    session['redis_db'] = settings.REDIS_DB
    session['redis_host'] = settings.REDIS_HOST
    session['redis_port'] = settings.REDIS_PORT

@app.route('/logout/')
def logout():
    if session:
        for key in session.keys():
            session.pop(key)

    return redirect(url_for('index'))

@app.route('/change_db', methods=['GET', 'POST'])
def change_db():
    """
    View to handle changing the redis db. Make sure val is an int
    and within the redis db range.
    """
    if request.method == 'POST':
        try:
            db = int(request.form['redis_db'])
        except ValueError:
            return redirect(url_for('index'))

        if db in xrange(0,10):
            session['redis_db'] = db
            flash('Redis DB changed to ' + str(db))
    return redirect(url_for('index'))

@app.route('/info/')
def info():
    """ View for info about your redis set up. """
    r = get_redis_connection(session)
    if not r:
        return redirect(url_for('setup'))

    info = r.info().items()

    return render_template('info.html', info=info)

@app.route('/setup/', methods=['GET', 'POST'])
def setup():
    """
    If a connection error with Redis occurs, users will be redirected
    here to setup the connection information.
    """
    if request.method == 'POST':
        host = request.form['host'] or settings.REDIS_HOST
        password = request.form['password']
        try:
            port = int(request.form['port'])
        except ValueError:
            port = settings.REDIS_PORT
            flash('Port number must be an integer. Default used.')

        session['redis_host'] = host
        session['redis_port'] = port
        session['redis_password'] = password

        return redirect(url_for('index'))


    return render_template('setup.html')

@app.route('/')
def index():
    """ All available keys. """
    if not session.has_key('redis_db'):
        set_session_defaults(session)
    r = get_redis_connection(session)

    if not r:
        return redirect(url_for('setup'))

    keys = r.keys()
    return render_template('index.html', keys=keys)

@app.route('/keys')
def keys():
    """ Get available keys. """
    if not session.has_key('redis_db'):
        set_session_defaults(session)
    r = get_redis_connection(session)

    if not r:
        return redirect(url_for('setup'))

    keys = r.keys()
    return jsonify(keys=keys)

@app.route('/key/<key>')
def key(key):
    """ Info for the key. """
    r = get_redis_connection(session)

    if not r:
        return redirect(url_for('setup'))

    if r.exists(key):
        rtype = r.type(key)
        if rtype == 'hash':
            output = r.hgetall(key)
        elif rtype == 'set':
            output = r.smembers(key)
        elif rtype == 'zset':
            output = r.zrange(key, 0, -1, withscores=True)
        elif rtype == 'list':
            output = [r.lindex(key, n) for n in xrange(r.llen(key))]
        else:
            output = r.get(key)
        return render_template('key.html', rtype=rtype, key=key, output=output,
            ttl=r.ttl(key))
    else:
        return render_template('no_key.html', key=key)

@app.route('/key/save/<key>', methods=['POST'])
def save(key):
    """ Update the value of a key. """
    r = get_redis_connection(session)

    if not r:
        return redirect(url_for('setup'))

    rtype = r.type(key)
    value = request.form['value']

    if rtype == 'hash':
        value = request.form['value'].strip("{}")
        values = [k.split(':', 1) for k in value.split(',')]

        r.delete(key)
        for k, v in values:
            r.hset(key, k.strip("' "), v.strip("' "))

    elif rtype == 'set':
        value = request.form['value'].strip("set([])")

        r.delete(key)
        for k in value.split(','):
            r.sadd(key, k.strip(" '\""))

    elif rtype == 'list':
        value = request.form['value'].strip("[]")

        r.delete(key)
        for k in value.split(','):
            r.rpush(key, k.strip().strip("'"))

    elif rtype == 'zset':
        value = request.form['value'].strip('[]')
        regex = re.compile('(?P<key>\(.*\))(?P<comma>,\s)(?P<value>\(.*\))')
        matches = re.search(regex, value)
        values = [match for match in matches.groups() if match != ', ']

        values_list = [k.split() for k in values]

        r.delete(key)
        for k, v in values_list:
            k, v = k.strip("(' ,)"), v.strip("(' ,)")
            r.zadd(key, k, v)

    elif rtype == 'string':
        r.set(key, value)

    return jsonify(
        flash=key + ' was saved successfully',
        value=value
    )

@app.route('/key/delete/<key>', methods=['GET'])
def delete(key):
    """ Delete key """
    r = get_redis_connection(session)

    if not r:
        return redirect(url_for('setup'))

    if r.exists(key):
        r.delete(key)
        return jsonify(flash="Key '" + key + "' was deleted successfully")
    else:
        return jsonify(flash="Key '" + key + "' was not found in Redis")

if __name__ == '__main__':
    app.run()

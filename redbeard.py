"""
TODO
"""
__author__ = "Chris Jones, Kenneth Love"
__version__ = "0.8.5"
__license__ = "MIT"

import re

from flask import (Flask, render_template, redirect, url_for, request, flash,
    session, jsonify)
from flask.views import MethodView

from flaskext.wtf import Form, TextField, Required, IntegerField, FloatField

import redis
from redis.exceptions import ConnectionError, ResponseError

import settings

SECRET_KEY = "781b0650af13493089a6ffafac755a61"

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True

# Forms
class KeyForm(Form):
    key_name = TextField('Key', validators=[Required()])
    key_ttl = IntegerField('TTL')

class StringForm(KeyForm):
    key_value = TextField('Value', validators=[Required()])

class ListSetForm(KeyForm):
    """
    Form for creating a new set or list
    """
    member = TextField('Member', validators=[Required()])

class HashForm(KeyForm):
    """
    Form for creating a hash.
    """
    member_name = TextField('Member', validators=[Required()])
    member_value = TextField('Value', validators=[Required()])

class ZSetForm(KeyForm):
    """
    Form for creating a ZSet
    """
    member_name = TextField('Member', validators=[Required()])
    member_score = FloatField('Score', validators=[Required()])

# Context processors
@app.context_processor
def get_db_size():
    r = get_redis_connection(session)
    if not r:
        return {'db_size':0}

    return dict(db_size=r.dbsize())

class Key(object):
    def __init__(self, *args, **kwargs):
        self.type = kwargs.get("type")
        self.id = kwargs.get("id")
        self.value = kwargs.get("value")


class KeyAPI(MethodView):
    template_name = "detail.html"

    def _get_key(self, key_id):
        r = get_redis_connection(session)
        key_type = r.type(key_id)

        if key_type == "string":
            value = r.get(key_id)
            return Key(type="string", id=key_id, value=value)
        elif key_type == "hash":
            value = r.hgetall(key_id)
            return Key(type="hash", id=key_id, value=value)
        elif key_type == "list":
            value = r.lrange(key_id, 0, r.llen(key_id))
            return Key(type="list", id=key_id, value=value)
        elif key_type == "set":
            value = r.smembers(key_id)
            return Key(type="set", id=key_id, value=value)
        elif key_type == "zset":
            value = r.zrange(key_id, 0, r.zcard(key_id), "WITHSCORES")
            return Key(type="zset", id=key_id, value=value)
        else:
            return None

    def get(self, key_id):
        key = None
        if key_id:
            key = self._get_key(key_id)
        return render_template(self.template_name, key=key)

    def post(self, key_id):
        return render_template(self.template_name)

key_view = KeyAPI.as_view("key_view")
app.add_url_rule("/keys/", defaults={"key_id": None}, view_func=key_view,
    methods=["GET",])
app.add_url_rule("/keys/", view_func=key_view, methods=["POST",])
app.add_url_rule("/keys/<string:key_id>", view_func=key_view,
    methods=["GET", "PUT", "DELETE"])


# Control app flow
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
    return redirect(request.referrer)

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

# Static views
@app.route('/info/')
def info():
    """ View for info about your redis set up. """
    r = get_redis_connection(session)
    if not r:
        return redirect(url_for('setup'))

    info = r.info().items()

    return render_template('info.html', info=info)

@app.route('/')
def index():
    """ All available keys. """
    if not session.has_key('redis_db'):
        set_session_defaults(session)
    r = get_redis_connection(session)

    if not r:
        return redirect(url_for('setup'))

    return render_template('index.html')

@app.route('/keys')
@app.route('/keys/<int:amount>')
def keys(amount=500):
    """ Get available keys. """
    if not session.has_key('redis_db'):
        set_session_defaults(session)
    r = get_redis_connection(session)

    if not r:
        return redirect(url_for('setup'))

    total_keys = len(r.keys())
    initial_keys = r.keys()[:amount]
    return jsonify(total_keys=total_keys, initial_keys=initial_keys)

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

# Read/write views
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

    key_changed = 'false'
    if request.form['key_name'] != request.form['saved_key_name']:
        r.rename(key, request.form['key_name'])
        key = request.form['key_name']
        key_changed = 'true'

    return jsonify(
        flash=key + ' was saved successfully',
        value=value,
        key=key,
        key_changed=key_changed
    )

@app.route('/key/new/string', methods=['GET', 'POST'])
def new_string():
    form = StringForm(request.form or None)

    if form.validate_on_submit():
        key = request.form['key_name']
        value = request.form['key_value']
        ttl = int(request.form['key_ttl'])

        r = get_redis_connection(session)
        if not r:
            return redirect(url_for('setup'))

        if r.exists(key):
            flash('%s already exists, edit it below' % key)
            return redirect('#%s' % key)

        try:
            r.set(key, value)
            if ttl and ttl != 0:
                r.expire(key, ttl)

            flash('%s was saved successfully.' % key)
            return redirect('#%s' % key)
        except:
            return jsonify(flash=key + ' failed to save.')
    else:
        return render_template('new_string.html', form=form)

@app.route('/key/new/set', methods=['GET', 'POST'])
def new_set():
    """
    View for creating a new set/member
    """
    form = ListSetForm(request.form or None)
    if form.validate_on_submit():
        key = request.form['key_name']
        ttl = int(request.form['key_ttl'])

        r = get_redis_connection(session)
        if not r:
            return redirect(url_for('setup'))

        for m in [k for k in request.form.keys() if k.startswith('member')]:
           r.sadd(key, request.form[m])

        if ttl and ttl != 0:
            r.expire(key, ttl)

        flash('%s was created.' % key)
        return redirect('#%s' % key)

    return render_template('new_set.html', form=form)

@app.route('/key/new/list', methods=['GET', 'POST'])
def new_list():
    """
    View for creating a new list with members.
    """
    form = ListSetForm(request.form or None)
    if form.validate_on_submit():
        key = request.form['key_name']
        ttl = int(request.form['key_ttl'])

        r = get_redis_connection(session)
        if not r:
            return redirect(url_for('setup'))

        for m in [k for k in request.form.keys() if k.startswith('member')]:
           r.rpush(key, request.form[m])

        if ttl and ttl != 0:
            r.expire(key, ttl)

        flash('%s was created.' % key)
        return redirect('#%s' % key)

    return render_template('new_list.html', form=form)

@app.route('/key/new/hash', methods=['GET', 'POST'])
def new_hash():
    """
    View for creating a new list with members.
    """
    form = HashForm(request.form or None)
    if form.validate_on_submit():
        key = request.form['key_name']
        ttl = int(request.form['key_ttl'])

        r = get_redis_connection(session)
        if not r:
            return redirect(url_for('setup'))

        for m in [k for k in request.form.keys() if k.startswith('member_name')]:
            v = re.sub('name', 'value', m)
            r.hset(key, request.form[m], request.form[v])

        if ttl and ttl != 0:
            r.expire(key, ttl)

        flash('%s was created.' % key)
        return redirect('#%s' % key)

    return render_template('new_hash.html', form=form)

@app.route('/key/new/zset', methods=['GET', 'POST'])
def new_zset():
    """
    View for creating a new zset
    """
    form = ZSetForm(request.form or None)
    if form.validate_on_submit():
        key = request.form['key_name']
        ttl = int(request.form['key_ttl'])

        r = get_redis_connection(session)
        if not r:
            return redirect(url_for('setup'))

        for m in [k for k in request.form.keys() if k.startswith('member_name')]:
            v = re.sub('name', 'score', m)
            r.zadd(key, request.form[m], float(request.form[v]))

        if ttl and ttl != 0:
            r.expire(key, ttl)

        flash('%s was created.' % key)
        return redirect('#%s' % key)

    return render_template('new_zset.html', form=form)

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

@app.route('/search/<string>', methods=['GET'])
@app.route('/search/', methods=['GET'])
def search(string=None):
    """ Find keys matching a string. """
    r = get_redis_connection(session)

    if not r:
        return redirect(url_for('setup'))
    if string:
        search_string = '*' + string + '*'
    else:
        search_string = '*'

    return jsonify(keys=r.keys(pattern=search_string))

if __name__ == '__main__':
    app.run()

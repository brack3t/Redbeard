from flask import Flask, render_template, redirect, url_for, request, flash
from flask import session
import redis
import settings

SECRET_KEY = '781b0650af13493089a6ffafac755a61'

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True

def get_redis_connection(session):
    """ Get Redis connection with session values """
    return redis.Redis(host=session['redis_host'], port=session['redis_port'],
        db=session['redis_db'])

def set_session_defaults(session):
    """ Setup default session """
    session['redis_db'] = settings.REDIS_DB
    session['redis_host'] = settings.REDIS_HOST
    session['redis_port'] = settings.REDIS_PORT

@app.route('/logout/')
def logout():
    if session.has_key('redis_db'):
        session.pop('redis_db', None)
    return redirect(url_for('index'))

@app.route('/change_db', methods=['GET', 'POST'])
def change_db():
    """
    View to handle changing the redis db. Make sure val is an int
    and withing the redis db range.
    """
    if request.method == 'POST':
        try:
            db = int(request.form['redis_db'])
        except ValueError:
            return redirect(url_for('index'))

        if db >= 0 and db <= 9:
            session['redis_db'] = db
            flash('Redis DB changed to ' + str(db))
    return redirect(url_for('index'))


@app.route('/info/')
def info():
    """ View for info about your redis set up. """
    r = get_redis_connection(session)
    info = r.info().items()

    return render_template('info.html', info=info)

@app.route('/')
def index():
    """ All available keys. """
    if not session.has_key('redis_db'):
        set_session_defaults(session)
    r = get_redis_connection(session)

    keys = r.keys()
    return render_template('index.html', keys=keys)

@app.route('/key/<key>')
def key(key):
    """ Info for the key. """
    r = get_redis_connection(session)

    rtype = r.type(key)
    if rtype == 'hash':
        output = r.hgetall(key)
    elif rtype == 'set':
        output = r.smembers(key)
    elif rtype == 'zset':
        output = r.zrange(key, 0, -1, withscores=True)
    else:
        output = r.get(key)
    return render_template('key.html', rtype=rtype, key=key, output=output)

@app.route('/key/save/<key>', methods=['POST'])
def save(key):
    """ Update the value of a key. """
    r = get_redis_connection(session)

    rtype = r.type(key)
    value = request.form['value']

    if rtype == 'hash':
        r.delete(key)

        value = request.form['value'].strip("{}")
        values = [k.split(':', 1) for k in value.split(',')]
        for k, v in values:
            r.hset(key, k.strip("' "), v.strip("' "))

    elif rtype == 'string':
        r.set(key, value)

    flash(key + ' was saved successfully')

    return redirect(url_for('key', key=key))

if __name__ == '__main__':
    app.run()

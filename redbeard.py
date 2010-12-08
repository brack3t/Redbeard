from flask import Flask, render_template, redirect, url_for, request, flash
import redis
import settings

SECRET_KEY = '781b0650af13493089a6ffafac755a61'

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True

r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
    db=settings.REDIS_DB)

@app.route('/info/')
def info():
    """ View for info about your redis set up. """
    return render_template('info.html', info=r.info().items())

@app.route('/')
def index():
    """ All available keys. """
    keys = r.keys()
    return render_template('index.html', keys=keys)

@app.route('/key/<key>')
def key(key):
    """ Info for the key. """
    rtype = r.type(key)
    if rtype == 'hash':
        output = r.hgetall(key)
    elif rtype == 'set':
        output = r.smembers(key)
    elif rtype == 'zset':
        output = r.zrange(key, 0, -1, withscores=True)
    else:
        output = r.get(key)
    return render_template('key.html', key=key, output=output)

@app.route('/key/save/<key>', methods=['POST'])
def save(key):
    """ Update the value of a key. """
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

from flask import Flask, render_template, redirect, url_for, request, flash
import redis

SECRET_KEY = '781b0650af13493089a6ffafac755a61'

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True

r = redis.Redis()

@app.route('/')
def index():
    keys = r.keys()
    return render_template('index.html', keys=keys)

@app.route('/key/<key>')
def key(key):
    rtype = r.type(key)
    if rtype == 'hash':
        output = r.hgetall(key)
    elif rtype == 'set':
        output = r.smembers(key)
    else:
        output = r.get(key)
    return render_template('key.html', key=key, output=output)

@app.route('/info/')
def info():
    return render_template('info.html', info=r.info().items())

@app.route('/key/save/<key>', methods=['POST'])
def save(key):
    rtype = r.type(key)
    value = request.form['value']

    if rtype == 'hash':
        r.delete(key)
        r.hset(key, value)
    elif rtype == 'string':
        r.set(key, value)
        flash(key + ' was saved successfully')

    return redirect(url_for('key', key=key))

if __name__ == '__main__':
    app.run()

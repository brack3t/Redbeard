from flask import Flask, render_template, redirect, url_for, request
import redis
app = Flask(__name__)
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

@app.route('/key/save/<key>', methods=['POST'])
def save(key):
    rtype = r.type(key)
    value = request.form['value'].strip('{}')
    new_value = dict([kv.split(':') for kv in value])

    return ', '.join(new_value.keys())
    if rtype == 'hash':
        #r.delete(key)
        #r.set(key, request.form['value'])
        #r.set(key, "{'balls':'lick them'}")
        pass

    return redirect(url_for('key', key=key))

if __name__ == '__main__':
    app.run()

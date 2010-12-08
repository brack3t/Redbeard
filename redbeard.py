from flask import Flask, render_template
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
    if r.type(key) == 'hash':
        output = r.hgetall(key)
    else:
        output = r.get(key)
    return render_template('key.html', key=key, output=output)

if __name__ == '__main__':
    app.run()

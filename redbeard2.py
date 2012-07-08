"""
TODO
"""
__author__ = "Chris Jones, Kenneth Love"
__version__ = "0.8.5"
__license__ = "MIT"

from flask import Flask, render_template, request, session
from flask.views import MethodView
from werkzeug.contrib.fixers import ProxyFix

import redis
from redis.exceptions import ConnectionError, ResponseError

import simplejson as json

import settings

SECRET_KEY = "781ba680hf13493089a6ffafac755a61"

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True
app.wsgi_app = ProxyFix(app.wsgi_app)


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

    def _get_keys(self, partial=None):
        partial = partial or ''
        r = get_redis_connection(session)
        r_keys = r.keys("%s*" % partial)
        return [self._get_key(k) for k in r_keys]

    def _set_key(self, key_id, key_type, key_value):
        r = get_redis_connection(session)

        if key_type == "string":
            r.set(key_id, key_value)
            return self._get_key(key_id)
        elif key_type == "hash":
            values = json.loads("%s" % key_value)
            for key, value in values:
                r.hset(key_id, key, value)
            return self._get_key(key_id)
        return None

    def get(self, partial=None):
        partial = partial or ''

        keys = self._get_keys(partial)

        if len(keys) == 1:
            return render_template(self.template_name, key=keys[0])
        else:
            return render_template("list.html", keys=keys)

    def post(self):
        return render_template(self.template_name)

    def put(self, partial=None):
        key_type = request.values.get("type", "string")
        key_id = request.values.get("id")
        key_value = request.values.get("value")

        key = self._set_key(key_id, key_type, key_value)
        return render_template(self.template_name, key=key)

key_view = KeyAPI.as_view("key_view")
app.add_url_rule("/api/keys", defaults={"partial": None}, view_func=key_view,
    methods=["GET"])
app.add_url_rule("/api/keys", view_func=key_view, methods=["POST"])
app.add_url_rule("/api/keys/<string:partial>", view_func=key_view,
    methods=["GET", "PUT", "DELETE"])


# Control app flow
def get_redis_connection(session):
    """
    Get Redis connection with session values. Ping Redis
    to make sure connection is working.
    """
    r = redis.Redis(
        host=session.get("redis_host", settings.REDIS_HOST),
        port=session.get("redis_port", settings.REDIS_PORT),
        db=session.get("redis_db", settings.REDIS_DB),
        password=session.get("redis_password", ''))

    try:
        r.ping()
    except (ConnectionError, ResponseError):
        return None

    return r

def set_session_defaults(session):
    """
    Setup default session
    """
    session["redis_db"] = getattr(settings, "REDIS_DB", 0)
    session["redis_host"] = getattr(settings, "REDIS_HOST", "127.0.0.1")
    session["redis_port"] = getattr(settings, "REDIS_PORT", 6379)

def index():
    if "redis_db" not in session:
        set_session_defaults(session)
    get_redis_connection(session)

    return render_template("index.html")
app.add_url_rule("/", view_func=index)

if __name__ == "__main__":
    app.run()
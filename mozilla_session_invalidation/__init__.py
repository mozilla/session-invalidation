from flask import Flask

app = Flask(__name__)

app.config.from_object('mozilla_session_invalidation.default_settings')
app.config.from_envvar('MOZILLA_SESSION_INVALIDATION_SETTINGS')

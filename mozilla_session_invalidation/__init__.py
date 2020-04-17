from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

app.config.from_object('mozilla_session_invalidation.default_settings')
app.config.from_envvar('MOZILLA_SESSION_INVALIDATION_SETTINGS')

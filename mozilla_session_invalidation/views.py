import typing as types

from flask import render_template, request

from mozilla_session_invalidation import app, socketio
import mozilla_session_invalidation.messages as msgs


def generate_id(is_unique: types.Callable[[str], bool]) -> str:
    '''
    '''

    return ''


@app.route('/')
def index():
    app.logger.warning('sample message')
    return render_template('index.html')


@app.route('/terminate', methods=['POST'])
def terminate():
    # TODO:  Store a list of all job IDs in the app global context.
    new_id = generate_id(lambda _: True)

    # TODO:  Retrieve OAuth credentials from request cookies.
    oauth_tkn = ''

    return msgs.Result([]).to_json()

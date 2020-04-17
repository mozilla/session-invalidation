import typing as types

from flask import render_template, request, session
from flask_socketio import emit

from mozilla_session_invalidation import app, socketio
import mozilla_session_invalidation.messages as msgs
from mozilla_session_invalidation.session_invalidation import JobManager


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
    app.logger.warning('Terminate received: {}'.format(request.json))
    return {'error': None}


@socketio.on('connect')
def handle_connection():
    # TODO:  Store a list of all job IDs in the app global context.
    new_id = generate_id(lambda _: True)

    # TODO:  Retrieve OAuth credentials from request cookies.
    oauth_tkn = ''

    session.job_manager = JobManager.new(new_id, request.sid, oauth_tkn)

    emit(
        msgs.WSMessage.JOB_ID_CREATED.value,
        msgs.JobCreated(new_id, session.job_manager.rp_states).to_json())

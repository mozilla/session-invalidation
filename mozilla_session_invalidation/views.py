import typing as types

from flask import render_template, request, session

from mozilla_session_invalidation import app, socketio
import mozilla_session_invalidation.messages as msgs
from mozilla_session_invalidation.session_invalidation import\
    SupportedReliantParties,\
    TerminationState


def generate_id(is_unique: types.Callable[[str], bool]) -> str:
    '''
    '''

    return 'testid'


@app.route('/')
def index():
    app.logger.warning('sample message')
    return render_template('index.html')


@app.route('/terminate', methods=['POST'])
def terminate():
    # TODO:  Store a list of all job IDs in the app global context.
    session['job_id'] = generate_id(lambda _: True)

    # TODO:  Retrieve OAuth credentials from request cookies.
    oauth_tkn = ''

    return msgs.NewJob(session['job_id']).to_json()


@app.route('/status')
def status():
    job_id = request.args['jobId']

    if session['job_id'] != job_id:
        return msgs.Error('Invalid job ID').to_json()

    return msgs.Result([
        msgs.Status(
            affected_rp=SupportedReliantParties.SSO,
            current_state=TerminationState.TERMINATED,
            output=None,
            error=None)
    ]).to_json()

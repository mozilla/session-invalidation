import typing as types

from flask import render_template, request, session

from mozilla_session_invalidation import app, socketio
import mozilla_session_invalidation.messages as msgs
from mozilla_session_invalidation.session_invalidation import\
    SupportedReliantParties,\
    TerminationState


@app.route('/')
def index():
    app.logger.warning('sample message')
    return render_template('index.html')


@app.route('/terminate', methods=['POST'])
def terminate():
    # TODO:  Retrieve OAuth credentials from request cookies.
    oauth_tkn = ''

    return msgs.Result([
        msgs.Status(
            affected_rp=SupportedReliantParties.SSO,
            current_state=TerminationState.TERMINATED,
            output='Test output',
            error='Test error',
        ),
    ]).to_json()

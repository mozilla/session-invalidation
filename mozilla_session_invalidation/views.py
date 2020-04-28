import typing as types

from flask import render_template, request, session

from mozilla_session_invalidation import app, socketio
import mozilla_session_invalidation.messages as msgs
import mozilla_session_invalidation.session_invalidation as sesinv


@app.route('/')
def index():
    app.logger.warning('sample message')
    return render_template('index.html')


@app.route('/terminate', methods=['POST'])
def terminate():
    # TODO:  Retrieve OAuth credentials from request cookies.
    oauth_tkn = ''

    try:
        username = request.json().get('username')
    except Exception:
        return msgs.Error('Invalid request').to_json()

    if username is None:
        return msgs.Error('Missing `username` field').to_json()

    jobs = _configure_jobs(oauth_tkn)

    results = []

    for rp, job in jobs.items():
        result = job(username)

        results.append(msgs.Status(
            affected_rp=rp,
            current_state=result.new_state,
            output=result.output,
            error=result.error,
        ))

    return msgs.Result(results).to_json()


def _configure_jobs(
    oauth_token: str
) -> types.Dict[sesinv.SupportedReliantParties, sesinv.IJob]:
    sso = sesinv.terminate_sso(sesinv.TerminateSSOConfig(oauth_token))

    return {
        sesinv.SupportedReliantParties.SSO: sso,
    }

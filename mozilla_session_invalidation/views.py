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

    # TODO: Retrieve AWS credentials from config.
    access_key_id = ''
    secret_key = ''

    # TODO: Figure out what we even need for GCP.
    gcp_token = ''

    try:
        username = request.json.get('username')
    except Exception:
        return msgs.Error('Invalid request').to_json()

    if username is None:
        return msgs.Error('Missing `username` field').to_json()

    jobs = _configure_jobs(oauth_tkn, access_key_id, secret_key, gcp_token)

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
    oauth_token: str,
    aws_access_key_id: str,
    aws_secret_key: str,
    gcp_token: str,
) -> types.Dict[sesinv.SupportedReliantParties, sesinv.IJob]:
    sso = sesinv.terminate_sso(sesinv.TerminateSSOConfig(oauth_token))
    gsuite = sesinv.terminate_gsuite(sesinv.TerminateGSuiteConfig(oauth_token))
    slack = sesinv.terminate_slack(sesinv.TerminateSlackConfig(oauth_token))
    aws = sesinv.terminate_aws(sesinv.TerminateAWSConfig(
        aws_access_key_id,
        aws_secret_key,
    ))
    gcp = sesinv.terminate_gcp(sesinv.TerminateGCPConfig(gcp_token))

    return {
        sesinv.SupportedReliantParties.SSO: sso,
        sesinv.SupportedReliantParties.GSUITE: gsuite,
        sesinv.SupportedReliantParties.SLACK: slack,
        sesinv.SupportedReliantParties.AWS: aws,
        sesinv.SupportedReliantParties.GCP: gcp,
    }

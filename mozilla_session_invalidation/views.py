import typing as types

from flask import render_template, request, session

from mozilla_session_invalidation import app, socketio
import mozilla_session_invalidation.messages as msgs
import mozilla_session_invalidation.session_invalidation as sesinv


# TODO : Move these into settings
MOZ_OAUTH_ENDPT = 'https://auth.mozilla.auth0.com/api/v2/users/{}/multifactor/actions/invalidate-remember-browser'
GSUITE_USERS_ENDPT = 'https://www.googleapis.com/admin/directory/v1/users/{}'
SLACK_LOOKUP_USER_ENDPT = 'https://slack.com/api/users.lookupByEmail'
SLACK_SCIM_USERS_ENDPT = 'https://api.slack.com/scim/v1/Users'

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
    sso = sesinv.terminate_sso(oauth_token, MOZ_OAUTH_ENDPT)
    gsuite = sesinv.terminate_gsuite(oauth_token, GSUITE_USERS_ENDPT)
    slack = sesinv.terminate_slack(
        oauth_token,
        SLACK_LOOKUP_USER_ENDPT,
        SLACK_SCIM_USERS_ENDPT,
    )
    aws = sesinv.terminate_aws(aws_access_key_id, aws_secret_key)
    gcp = sesinv.terminate_gcp(gcp_token)

    return {
        sesinv.SupportedReliantParties.SSO: sso,
        sesinv.SupportedReliantParties.GSUITE: gsuite,
        sesinv.SupportedReliantParties.SLACK: slack,
        sesinv.SupportedReliantParties.AWS: aws,
        sesinv.SupportedReliantParties.GCP: gcp,
    }

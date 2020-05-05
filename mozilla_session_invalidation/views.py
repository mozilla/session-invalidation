import typing as types

from flask import g as flask_global, render_template, request, session

from mozilla_session_invalidation import app
import mozilla_session_invalidation.authentication as auth
import mozilla_session_invalidation.messages as msgs
import mozilla_session_invalidation.session_invalidation as sesinv


# TODO : Move these into settings
MOZ_OAUTH_ENDPT = 'https://auth-dev.mozilla.auth0.com/api/v2/users/{}/multifactor/actions/invalidate-remember-browser'
GSUITE_USERS_ENDPT = 'https://www.googleapis.com/admin/directory/v1/users/{}'
SLACK_LOOKUP_USER_ENDPT = 'https://slack.com/api/users.lookupByEmail'
SLACK_SCIM_USERS_ENDPT = 'https://api.slack.com/scim/v1/Users'

@app.route('/')
def index():
    app.logger.warning('sample message')
    return render_template('index.html')


@app.route('/terminate', methods=['POST'])
def terminate():
    try:
        username = request.json.get('username')
    except Exception:
        return msgs.Error('Invalid request').to_json()

    if username is None:
        return msgs.Error('Missing `username` field').to_json()

    jobs = _configure_jobs(app.config)

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


JobConfig = types.Dict[sesinv.SupportedReliantParties, sesinv.IJob]

def _configure_jobs(config) -> JobConfig:
    sso_creds = auth.SSOCreds(
        client_id=config['SSO_CLIENT_ID'],
        client_secret=config['SSO_CLIENT_SECRET'],
        auth_url=config['SSO_AUTH_URL'],
        audience=config['SSO_AUDIENCE'],
        grant_type=config['SSO_GRANT_TYPE'],
    )
    sso_id_fmt = config['SSO_ID_FORMAT']
    sso = sesinv.terminate_sso(sso_creds, sso_id_fmt, MOZ_OAUTH_ENDPT)

    gsuite_oauth_token = ''
    gsuite = sesinv.terminate_gsuite(gsuite_oauth_token, GSUITE_USERS_ENDPT)

    slack_oauth_token = config['SLACK_TOKEN']
    slack = sesinv.terminate_slack(
        slack_oauth_token,
        SLACK_LOOKUP_USER_ENDPT,
        SLACK_SCIM_USERS_ENDPT,
    )

    aws_access_key_id = ''
    aws_secret_key = ''
    aws = sesinv.terminate_aws(aws_access_key_id, aws_secret_key)

    gcp_token = ''
    gcp = sesinv.terminate_gcp(gcp_token)

    return {
        sesinv.SupportedReliantParties.SSO: sso,
        sesinv.SupportedReliantParties.GSUITE: gsuite,
        sesinv.SupportedReliantParties.SLACK: slack,
        sesinv.SupportedReliantParties.AWS: aws,
        sesinv.SupportedReliantParties.GCP: gcp,
    }

# session-invalidation

The Mozilla Session Invalidation tool (name subjet to change) is a solution
providing Information Security teams such as Mozilla's Enterprise
Information Security (EIS) with the capability to rapidly terminate the
sessions of user accounts across a variety of reliant parties (RPs), i.e.
services that a user may have a session on.  In doing so, a potentially
compromised user account can have its access to services revoked, preventing an
attacker from using a compromised account to wreak havoc.

![Early demo image](https://raw.githubusercontent.com/mozilla/session-invalidation/master/docs/images/earlydemo.png)

The Session Invalidation tool is implemented as a web application powered on
the frontend by [VueJS](https://vuejs.org/) and by
[Flask](https://flask.palletsprojects.com/en/1.1.x/) on the backend.

A user need only provide the email address of the user whose accounts they
wish to terminate, granted that this email address is tied to each of the
supported RPs.

## Supported Reliant Parties

At the time of this writing two RPs are supported: SSO and Slack.

### Single Sign-On

Many organizations use SSO to manage access to a variety of other RPs like JIRA.
If a user's SSO session were compromised, the attacker in question would have
access to each of the RPs protected by SSO.  By terminating a compromised user's
SSO session, we can contain this issue and prevent an attacker from getting
access to any RPs that they have not already compromised sessions for.

Terminating access to individual RPs beyond this point must be done on a
service-by-service basis, and this tool makes it relatively easy to implement
new functionality to do just that.

### Slack

Where Slack is used by organizations for sensitive communications and file
sharing, a compromised Slack user account could lead to an attacker phishing
other users, downloading files and obtaining sensitive information.  The
session invalidation tool is able to immediately log a user out of Slack,
forcing the account owner who knows the account password and, ideally, owns
the account's associated MFA device to log back in, eliminating the attacker's
presence from the Slack account.

## Development

The Session Invalidation tool (name subject to change) is currently in an early
and active stage of development.  The backend API is not likely to undergo any
change in the near future, however its interface is described in
[docs/api.md](https://github.com/mozilla/session-invalidation/blob/master/docs/api.md).

Adding support for new RPs can be done in a fairly modular fashion, and a guide
explaining all of the changes that need to take place to support terminating
sessions for a new RP in both the backend and frontend an be found in
[docs/supporting_new_rps.md](https://github.com/mozilla/session-invalidation/blob/master/docs/supporting_new_rps.md).

## Deployment

The Session Invalidation tool runs in AWS Lambda, depending on an AWS SSM
parameter to store secrets and AWS S3 to host static content for the frontend.
All of the steps to create these resources and deploy the application can be
found in the [deployment guide](/docs/deployment.md).

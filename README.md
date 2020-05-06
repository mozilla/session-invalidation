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

## Project Roadmap

Until the end of July, the roadmap for the project consists of the following
milestones:

1. Implement support for the termination of GSuite user sessions.
2. Add functionality to have use of the tool emitted e.g. to
   [Amazon SQS](https://aws.amazon.com/sqs/) for consumption by a SIEM such as
   [MozDef](https://github.com/mozilla/MozDef).
3. Produce documentation describing the tool, its architecture etc. and have
   this documentation reviewed and the tool assessed by Mozilla's EIS team.
4. Deploy and begin testing the tool running on an approved architecture.

Following these steps, further development on support for more RPs will take
place.

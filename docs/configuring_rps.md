# Configuring RPs

Each of the reliant parties (RPs) that the session invalidation application
supports must be set up to grant access to the app with the appropriate
permissions required to invoke their respective APIs.  This document briefly
explains the configurations required for each RP and what to do with the
credentials produced by each one.

## SSO

SSO for mozilla is backed by OAuth. To add support for session invalidation:

1. Create a client called "Session Invalidation"
2. Denote the owner to be the current maintainer of the session invalidation app
3. Provide access to the `update:users` scope
4. Copy the client id and client secret

The scope granted above grants access to things like:

  * Sending verification emails to users.
  * Modify user permissions.
  * Modify user roles.
  * Generate MFA recovery codes.

## Gsuite

In order to configure GSuite, as an admin user:

1. Create a project for the session invalidation application in GCP
2. Create a service account for the project
3. On the Service Accounts page, create a new JSON RSA key
4. Download the JSON key
5. Grant the project Domain Wide Delegation access in admin console.
6. Grant the service account the scope “https://www.googleapis.com/auth/admin.directory.user”
7. Note the email address of the GSuite admin user that created everything

The admin email will become the `GSUITE_SUBJECT` configuration parameter in
`serverless.yml`.

The scope granted above, combined with access to the Admin SDK grants the
project access to the entire user administration API including:

  * The ability to create, delete and modify users.
  * The ability to promote a user to an administrator.

## GCP

GCP session termination works the same way as and requires a configuration
identitcal to that of GSuite, albeit the values from the JSON RSA key
are encoded into distinct configuration variables.

In Mozilla's environment, we have a GSuite configuration for `@mozilla.com`
and a separate GCP configuration for `@gcp.infra.mozilla.com`.

## Slack

In order to configure Slack to obtain credentials for the session invalidation
app:

1. Create an application with the following OAuth user scopes:
    * `admin`
    * `users:read`
    * `users:read.email`
2. On the app home page, navigate to **OAuth & Permissions** page
3. Copy the **OAuth Access Token**

Note that the scopes granted above grants access to things such as:

  * The [SCIM Users API](https://api.slack.com/scim#access).
  * The ability to read user profile information and specifically emails.

The ability to perform more specific administrative actions on users and a
workspace requires more scopes.

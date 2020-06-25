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

## Slack

In order to configure Slack to obtain credentials for the session invalidation
app:

1. Create an application with the following OAuth user scopes:
    * `admin`
    * `users:read`
    * `users:read.email`
2. On the app home page, navigate to **OAuth & Permissions** page
3. Copy the **OAuth Access Token**

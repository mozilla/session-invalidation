# Session Invalidation API

The Session Invalidation tool (name subject to change) has its backend
implemented in Python with [Flask](https://flask.palletsprojects.com/).
This document describes the endpoints that it exposes primarily for
the purpose of documenting the interface between the frontend UI and the
backend API.

As a conventionm, this document uses
[TypeScript](https://www.typescriptlang.org/docs/handbook/advanced-types.html)'s
type syntax to describe request parameters and response data.

## Common Types

The following type definitions may be reused throughout this document.

```typescript
type Error = { error: string }

type SupportedRP
  = 'sso'
  | 'gsuite'
  | 'slack'
  | 'aws'
  | 'gcp'

type State
  = 'not_modified'
  | 'terminated'
  | 'error'
  | 'not_implemented'
```

## Index page

```
GET /
```

The landing and main application page for the tool is served at the
root endpoint.  This endpoint will kick off the OIDC client authentication
process.  Upon successful authentication, a cookie is set in the user's
browser which enables access to the `/terminate` endpoint.

### Parameters

None

### Response

HTML

## OIDC callback URI

```
GET /callback
```

The user's browser is redirected to this endpoint by Mozilla OAuth as part
of the OIDC client flow.  It finalizes checks with OAuth that authentication
has taken place successfully and redirects the user back to the `/` endpoint
where the index page is served.

### Parameters

```typescript
type Parameters = {
  code: string,
  state: string,
}
```

The parameters to this endpoint are provided as URL parameters in the
redirect URI to this endpoint.

### Response

This endpoint stores a `user-session` cookie and redirects to `/` upon
successful authentication to OAuth.

## Fetch a static file

```
GET /static/{filename}
```

This endpoint will attempt to load a static file from an S3 bucket dedicated
to storing content for the Session Invalidation application.


### Parameters

The name of the file to retrieve is encoded into the path in place of
`{filename}`.

### Response

The contents of one of

* `index.html`
* `main.js`
* `styles.css`

which are specified in the URL.

## Terminate a user session

```
POST /terminate
```

All of the user sessions for each supported RP will be terminated
synchronously upon one request to the `/terminate` endpoint.  Access to this
endpoint depends on successful authentication to Mozilla OAuth via the
OIDC client flow initiated by the `/` endpoint.

### Parameters

```typescript
type Parameters = {
  username: string,
}
```

The `username` parameter is a string containing the email address of the user
whose sessions should be terminated.  For example, `"user@website.com"`.

### Response

```typescript
type Status = {
  affectedRP: SupportedRP,
  currentState: State,
  output: string | null,
  error: string | null,
}

type Result = {
  results: Array<Status>
}

type Response = Error | Result
```

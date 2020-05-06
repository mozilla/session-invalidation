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
root endpoint.

### Parameters

None

### Response

HTML

## Terminate a user session

```
POST /terminate
```

All of the user sessions for each supported RP will be terminated
synchronously upon one request to the `/terminate` endpoint.

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

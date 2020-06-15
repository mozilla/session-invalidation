# SQS Message Format

This document describes the format of messages sent by the Session Invalidation
application to Amazon SQS which are destined for MozDef.

## Format

All messages are JSON objects with the following
[types](https://www.typescriptlang.org/docs/handbook/advanced-types.html).

```typescript
// Identifiers for reliant parties supported by the session invalidation
// application.  In the case that a message describes the successful
// termination of a user's sessions, a list of these will be included
// to describe which RPs were successfully terminated.
type SupportedRP
  = "sso"
  | "slack"
  | "gsuite"
  | "aws"
  | "gcp"


// The type of messages written to SQS
type Message = {
  // This value is fixed and never changes.
  "category": "sessioninvalidation",

  "details": {
    // A generic message string.
    "logmessage": string,

    // The level of severity of the event the message describes.
    "loglevel": "notset" | "info" | "debug" | "warning" | "error" | "critical",

    // The email address of the user of the application.
    "actor": null | string,

    // The email address of the user whose sessions were terminated if
    // a termination event is being described, or else null.
    "invalidateduser": null | string, 

    // A list of identifiers for reliant parties that were 
    "invalidatedsessions": null | Array<SupportedRP>,
  }
}
```

## Examples

**A user's sessions were invalidated**

```typescript
{
  "category": "sessioninvalidation",
  "details": {
    "logmessage": "Terminated sessions for user@mozilla.com",
    "loglevel": "warning",
    "invalidateduser": "user@mozilla.com",
    "invalidatedsessions": ["sso", "slack"]
  }
}
```

**Someone accessed the session invalidation application**

_Note: Session Invalidation does not support SSO authentication at the time of
writing this, so we do not yet have access to requester information._

```typescript
{
  "category": "sessioninvalidation",
  "details": {
    "logmessage": "Session invalidation application requested",
    "loglevel": "info",
    "invalidateduser": null,
    "invalidatedsessions": null
  }
}
```

## Events of Interest

There are several events logged for consumption by MozDef that can be safely
disregarded until an investigation takes place.  However the following are
likely of high enough importance that alerts should be triggered when they are
observed.

### Scenario: Someone accesses the session invalidation application

This scenario is of interest because someone accessing the application is an
occurrence we would like to know about early.  This event is indicated by an
instrumentation message with a `details.logmessage` value of

> "Session Invalidation application requested"

and a `details.loglevel` of `"info"`.

### Scenario: Someone makes a request to the terminate endpoint

Rather than waiting for a potential attacker to succeed at terminating user
sessions, it may be prudent to alert when the terminate endpoint is requested.
This event is indicated by messages with `details.logmessage` and
`details.loglevel` values of

```json
{
  "logmessage": "Invalid request sent to terminate endpoint",
  "loglevel": "error"
}
```

```json
{
  "logmessage": "Request sent to terminate endpoint with missing username",
  "loglevel": "error"
}
```

```json
{
  "logmessage": "Request to terminate sessions for {username}",
  "loglevel": "warning"
}
```

```json
{
  "logmessage": "Terminated sessions for {username}",
  "loglevel": "warning"
}
```

A common feature of these messages is that the `logmessage` fields all contain
either the substring `"terminate"` or `"Terminate"`.  The events of particularly
high interest have `loglevel`s of `"warning"`.

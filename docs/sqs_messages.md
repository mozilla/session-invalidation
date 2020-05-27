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
    "loglevel": "info" | "debug" | "warning" | "error" | "exception",

    // The email address of the user whose sessions were terminated if
    // a termination event is being described, or else null.
    "invalidateduser": null | string, 

    // A list of identifiers for reliant parties that were 
    "invalidatedsessions": null | Array<SupportedRP>,
  }
}
```

Some examples:

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

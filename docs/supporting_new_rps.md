# Implementing Support for New RPs

This document explains how session termination for RPs is implemented and how
you can add functionality to the application backend and frontend to support
new RPs.

## Termination Functions

At the time of this writing, all of the functionality for session termination
across supported RPs is implemented in `sesinv/sessions.py`.  Here you will
find a couple of important types and conventions that you can use and follow to
implement support for new RPs that will easily work with the rest of the
application.

1. The `SupportedReliantParties` enumeration contains identifiers for RPs that
   are shared with the frontend.  That is, the value you put on the right side
   of the `=` sign will have to be known by the JavaScript portion of the
   application.  `snake_case` values are recommended for consistency.
2. The `JobResult` type is what a termination function ultimately returns
   to the REST API function that calls it.  This type allows you to express what
   state the user session moved into as well as any errors or output messages
   that should be displayed to the application's user.
3. The `IJob` type alias describes the interface that all termination functions
   are expected to present.  Because these functions must have consistent
   interfaces, you will notice that functions like `terminate_sso` in fact
   themselves return an `IJob`, a `_terminate` function constructed internally.
   This allows functions like `terminate_sso` to accept unique parameters that
   are required for the inner `_terminate` function while ultimately satisfying
   the `IJob` interface.  More on this later.

Given the above information, adding a new termination function requires the
following steps.  Supposing you wanted to support an "Imaginary RP", you would:

First, add a line to the definition of `SupportedReliantParties` such as

```py
    IMAGINARY_RP = 'imaginary_rp'
```

Second, define a function like the following

```py
def terminate_imaginary_rp(unqiue: int, parameters: str) -> IJob:
    def _terminate(email: UserEmail) -> JobResult:
        # Useful work and error handling happens here...

        return JobResult(TerminationState.TERMINATED)
```

And that's it!

## Integrating Termination Functions Into the Backend

Once a new termination function has been implemented, it must be configured for
use by the API backend.  This portion of the codebase organizes all of the work
of passing arguments from the application configuration into your termination
function's wrapper (e.g. `terminate_imaginary_rp`) in the `configure_jobs`
function in `sesinv/sessions.py`. `configure_jobs` returns a
dictionary mapping the identifier that you added to `SupportedReliantParties` to
an `IJob` function.  So, for example, you might set up your new function with
the following code additions to `configure_jobs`.  Note that `configure_jobs` is
called with a list of identifiers of RPs that the user would like to terminate,
and so your termination function should only be configured if it is selected.

```py
    if SupportedReliantParties.IMAGINARY_RP.value in selections:
      imaginary_rp = sesinv.terminate_imaginary_rp(
          config['UNIQUE'],
          config['PARAMETERS'],
      )

      configured[SupportedReliantParties.IMAGINARY_RP] = imaginary_rp
```

The last thing you'll need to add are definitions of the configuration variables
that your new code changes reference.  Add them to `serverless.yml`'s
`provider.environment` section.

```
UNIQUE: 32
PARAMETERS: 'value'
```

Note that any secret parameters must be configured once during deployment.
For information about how to do this, see [deployment.md](deployment.md).

With just these changes, your new termination function will be invoked every
time someone sends a valid, authenticated request to the `/terminate` endpoint.

## Adding Support to the Frontend

The last thing to add is support to the frontend application so that users will
be able to see output associated with the RP you are supporting.  All of the
code for the frontend exists in `static/main.js`.
This involves the following steps:

1. Adding the shared identifier you specified in your change to
   `SupportedReliantParties`.
2. Adding an enable/disable toggle.
3. Adding a column to the main output table to display the state of your RP's
   session.
4. Handling changes to the session state in the application logic.


The first step is very straightforward.  Toward the top of the file, you will
see the constant definitions of RP identifiers, such as `RP_SSO`.  Start by
adding a new constant for your RP.  Remember that this value **must** be the
same as the one you supplied to `SupportedReliantParties`.

```js
const RP_IMAGINARY = 'imaginary_rp'
```

Second, navigate to the definition the `supportedRPs` property of the
`TerminationForm` component's `data` method.  Add a new property to this object
with the identifier of your new RP and map it to an object with a string
representation and a boolean `enabled` field.  Since the toggle checkboxes are
checked by default, `enabled` should default to `true`.

```js
    supportedRPs: {
      [RP_IMAGINARY]: { repr: 'Imaginary', enabled: true },
    }
```

Next, find the `template` field of the `TerminationResults` component and
add a new table header element and table data cell for the table.

```html
        <!-- ... --> 
        <th>GCP</th>
        <th>Imaginary</th>
        
        <!-- ... -->
        <td>
          <span v-bind:data-state="state.imaginaryState">
            {{ representation(state.imaginaryState) }}
          </span>
        </td>
```

Last, the frontend must know to look for changes to the state of your imaginary
RP's session.  Inside the `TerminationResults` component, there are two methods
that must be updated.

The first is the `newJob` method, which constructs a simple object that tracks
updates to session states.  Simply add a new property to this object with the
same name that you useed in your new `<span>` tag above.

```js
    newJob(username) {
      return {
        // ...
        imaginaryState: STATE_NOT_MODIFIED,
      }
    }
```

The second method to update is `updateJob`, which applies changes to session
states as results are processed.

```js
    updateJob(job, result) {
      // ...
    } else if (result['affectedRP'] == RP_IMAGINARY) {
      job.imaginaryState = result['currentState']
    }
```

you will see the definition of a variable called `job` that initializes the
states for each RP.  Add a line to initialize a state for your new RP. Note that
the key (left side of `:` that you use must be the same as the one you
referenced in the `<span>` element you added to the template).

```js
        let job = {
          // ...
          imaginaryState: STATE_NOT_MODIFIED
```

You'll also see that this method checks each `result`'s `affectedRP` field to
determine the state changes to each RP.  Add a case for your new one.

```js
          } else if (result['affectedRP'] === RP_IMAGINARY) {
            job.imaginaryState = result['currentState']
          }
```

With these changes in place, the frontend has been informed about the new RP
that you are supporting and now contains the logic it needs to look for state
changes and to display them.

With this, you're done! The Session Invalidation tool (name subject to change)
now completely supports your new RP.

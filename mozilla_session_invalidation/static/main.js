(function () {
  const TERMINATE_ENDPT = '/terminate'
  const STATUS_UPDATE_INTERVAL = 500

  // Handles to document elements that contain inputs and outputs.
  const usernameInput = document.getElementById('username')
  const terminateButton = document.getElementById('terminate')
  const outputsList = document.getElementById('outputs')


  // Constant reliant party identifiers.
  const RP_SSO = 'sso'

  // Constant state name representations.
  const STATE_NOT_MODIFIED = 'not_modified'
  const STATE_TERMINATED = 'terminated'
  const STATE_ERROR = 'error'

  // Event handlers.  Each is registered at the end of the function.
 
  /**
   * Initiate a request to terminate a session for a user and register a
   * function to run in an interval to retrieve status updates.
   */
  const sendTerminateRequest = function (evt) {
    fetch(TERMINATE_ENDPT, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        username: usernameInput.value,
      }),
    })
    .then((response) => response.json())
    .then((data) => {
      const newItem = document.createElement('li')

      const content = document.createTextNode(JSON.stringify(data))

      newItem.appendChild(content)

      outputsList.appendChild(newItem)

      setInterval(statusUpdate(data['jobId']), STATUS_UPDATE_INTERVAL)
    })
  }

  /**
   * Construct a closure for a `setInterval` function that will retrieve updates
   * to a termination job and update the `outputsList`.
   */
  const statusUpdate = function (jobId) {
    let calls = 0

    return function () {
      calls += 1

      const newItem = document.createElement('li')

      const content = document.createTextNode('Calls: ' + calls)

      newItem.appendChild(content)

      outputsList.appendChild(newItem)
    }
  }

  // Event registration.

  terminateButton.addEventListener('click', sendTerminateRequest)
})()

(function () {
  const TERMINATE_ENDPT = '/terminate'
  const STATUS_ENDPT = '/status'
  const STATUS_UPDATE_INTERVAL = 500
  
  // Constant reliant party identifiers.
  const RP_SSO = 'sso'

  // Handles to document elements that contain inputs and outputs.
  const usernameInput = document.getElementById('username')
  const terminateButton = document.getElementById('terminate')
  const outputsList = document.getElementById('outputs')
  const reliantParties = {
    [RP_SSO]: document.getElementById(`rp-${RP_SSO}`),
  }

  // Constant state name representations.
  const STATE_NOT_MODIFIED = 'not_modified'
  const STATE_TERMINATED = 'terminated'
  const STATE_ERROR = 'error'

  // Utility functions.
  
  const finishedUpdating = function () {
    let finished = true

    for (rpName in reliantParties) {
      const state = reliantParties[rpName].getAttribute('data-state')

      finished = finished && (state === STATE_TERMINATED)
    }

    return finished
  }
  
  const addOutputItem = function (message, className) {
    const newItem = document.createElement('li')

    const content = document.createTextNode(message)

    newItem.classList.add(className)

    newItem.appendChild(content)

    outputsList.appendChild(newItem)
  }
  
  const output = function (message) {
    addOutputItem(message, 'output')
  }

  const error = function (message) {
    addOutputItem(message, 'error')
  }

  const updateStatusView = function (affectedRP, currentState) {
    reliantParties[affectedRP].setAttribute('data-state', currentState)
  }

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
      const intervalId = setInterval(
        () => statusUpdate(data['jobId'], intervalId),
        STATUS_UPDATE_INTERVAL)
    })
  }

  /**
   * Retrieve updates to the statuses of termination jobs.
   */
  const statusUpdate = function (jobId, intervalId) {
    if (finishedUpdating()) {
      clearInterval(intervalId)

      return
    }

    fetch(`${STATUS_ENDPT}?jobId=${jobId}`)
    .then((response) => response.json())
    .then((data) => {
      for (const result of data.results) {
        updateStatusView(result['affectedRP'], result['currentState'])

        if (result['output'] !== null) {
          output(result['output'])
        }
        if (result['error'] !== null) {
          error(result['error'])
        }
      }
    })
  }

  // Event registration.

  terminateButton.addEventListener('click', sendTerminateRequest)
})()

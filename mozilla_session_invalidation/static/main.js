const TerminationForm = {
  name: 'TerminationForm',
  template: `
    <div>
      <input v-model="username" id="username" placeholder="username@mozilla.com" type="text" />
      <input v-on:click="submitJob" id="terminate" value="Terminate" type="button" />
    </div>
  `,
  data: () => ({
    username: '',
  }),
  methods: {
    submitJob() {
      alert('Submitted')
    }
  }
}

const TerminationResults = {
  name: 'TerminationResults',
  template: `
    <table id="results">
      <tr>
        <th>Username</th>
        <th>SSO</th>
        <th>GSuite</th>
        <th>Slack</th>
        <th>AWS</th>
        <th>GCP</th>
      </tr>
      <tr v-for="state in userStates">
        <td class="username">
          {{ state.username }}
        </td>
        <td>
          <span v-bind:data-state="state.ssoState">
            {{ state.ssoState }}
          </span>
        </td>
        <td>
          <span v-bind:data-state="state.gsuiteState">
            {{ state.gsuiteState }}
          </span>
        </td>
        <td>
          <span v-bind:data-state="state.slackState">
            {{ state.slackState }}
          </span>
        </td>
        <td>
          <span v-bind:data-state="state.awsState">
            {{ state.awsState }}
          </span>
        </td>
        <td>
          <span v-bind:data-state="state.gcpState">
            {{ state.gcpState }}
          </span>
        </td>
      </tr>
    </table>
  `,
  data: () => ({
    userStates: [
      {
        username: 'tester@mozilla.com',
        ssoState: 'Terminated',
        gsuiteState: 'Not implemented',
        slackState: 'Not implemented',
        awsState: 'Not implemented',
        gcpState: 'Not implemented',
      },
      {
        username: 'another@mozilla.com',
        ssoState: 'Not modified',
        gsuiteState: 'Not implemented',
        slackState: 'Not implemented',
        awsState: 'Not implemented',
        gcpState: 'Not implemented',
      },
    ]
  }),
}

const StatusMessageList = {
  name: 'StatusMessageList',
  template: `
    <ul id="outputs">
    </ul>
  `,
}

const Application = {
  template: `
    <div>
      <TerminationForm></TerminationForm>
      <TerminationResults></TerminationResults>
      <StatusMessageList></StatusMessageList>
    </div>
  `,
  components: {
    TerminationForm,
    TerminationResults,
    StatusMessageList,
  }
}

const application = new Vue({
  el: '#application',
  components: {
    Application,
  }
})

//(function () {
//  const TERMINATE_ENDPT = '/terminate'
//  const STATUS_ENDPT = '/status'
//  const STATUS_UPDATE_INTERVAL = 500
//  
//  // Constant reliant party identifiers.
//  const RP_SSO = 'sso'
//
//  // Handles to document elements that contain inputs and outputs.
//  const usernameInput = document.getElementById('username')
//  const terminateButton = document.getElementById('terminate')
//  const outputsList = document.getElementById('outputs')
//  const reliantParties = {
//    [RP_SSO]: document.getElementById(`rp-${RP_SSO}`),
//  }
//
//  // Constant state name representations.
//  const STATE_NOT_MODIFIED = 'not_modified'
//  const STATE_TERMINATED = 'terminated'
//  const STATE_ERROR = 'error'
//
//  // Utility functions.
//  
//  const finishedUpdating = function () {
//    let finished = true
//
//    for (rpName in reliantParties) {
//      const state = reliantParties[rpName].getAttribute('data-state')
//
//      finished = finished && (state === STATE_TERMINATED)
//    }
//
//    return finished
//  }
//  
//  const addOutputItem = function (message, className) {
//    const newItem = document.createElement('li')
//
//    const content = document.createTextNode(message)
//
//    newItem.classList.add(className)
//
//    newItem.appendChild(content)
//
//    outputsList.appendChild(newItem)
//  }
//  
//  const output = function (message) {
//    addOutputItem(message, 'output')
//  }
//
//  const error = function (message) {
//    addOutputItem(message, 'error')
//  }
//
//  const updateStatusView = function (affectedRP, currentState) {
//    reliantParties[affectedRP].setAttribute('data-state', currentState)
//  }
//
//  // Event handlers.  Each is registered at the end of the function.
// 
//  /**
//   * Initiate a request to terminate a session for a user and register a
//   * function to run in an interval to retrieve status updates.
//   */
//  const sendTerminateRequest = function (evt) {
//    fetch(TERMINATE_ENDPT, {
//      method: 'POST',
//      headers: {
//        'Content-Type': 'application/json',
//      },
//      body: JSON.stringify({
//        username: usernameInput.value,
//      }),
//    })
//    .then((response) => response.json())
//    .then((data) => {
//      const intervalId = setInterval(
//        () => statusUpdate(data['jobId'], intervalId),
//        STATUS_UPDATE_INTERVAL)
//    })
//  }
//
//  /**
//   * Retrieve updates to the statuses of termination jobs.
//   */
//  const statusUpdate = function (jobId, intervalId) {
//    if (finishedUpdating()) {
//      clearInterval(intervalId)
//
//      return
//    }
//
//    fetch(`${STATUS_ENDPT}?jobId=${jobId}`)
//    .then((response) => response.json())
//    .then((data) => {
//      for (const result of data.results) {
//        updateStatusView(result['affectedRP'], result['currentState'])
//
//        if (result['output'] !== null) {
//          output(result['output'])
//        }
//        if (result['error'] !== null) {
//          error(result['error'])
//        }
//      }
//    })
//  }
//
//  // Event registration.
//
//  terminateButton.addEventListener('click', sendTerminateRequest)
//})

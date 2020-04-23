const TERMINATE_ENDPT = '/terminate'
const STATUS_ENDPT = '/status'
const STATUS_UPDATE_INTERVAL = 500


const STATE_NOT_MODIFIED = 'not_modified'
const STATE_TERMINATED = 'terminated'
const STATE_ERROR = 'error'
const STATE_NOT_IMPLEMENTED = 'not_implemented'


const STATE_REPRESENTATIONS = {
  [STATE_NOT_MODIFIED]: 'Not modified',
  [STATE_TERMINATED]: 'Terminated',
  [STATE_ERROR]: 'Error',
  [STATE_NOT_IMPLEMENTED]: 'Not implemented',
}


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
      this.$root.$emit('TerminateRequestSent', this.username)
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
            {{ representation(state.ssoState) }}
          </span>
        </td>
        <td>
          <span v-bind:data-state="state.gsuiteState">
            {{ representation(state.gsuiteState) }}
          </span>
        </td>
        <td>
          <span v-bind:data-state="state.slackState">
            {{ representation(state.slackState) }}
          </span>
        </td>
        <td>
          <span v-bind:data-state="state.awsState">
            {{ representation(state.awsState) }}
          </span>
        </td>
        <td>
          <span v-bind:data-state="state.gcpState">
            {{ representation(state.gcpState) }}
          </span>
        </td>
      </tr>
    </table>
  `,
  data: () => ({
    userStates: [
      {
        jobId: '',
        username: 'tester@mozilla.com',
        ssoState: STATE_TERMINATED,
        gsuiteState: STATE_NOT_IMPLEMENTED,
        slackState: STATE_NOT_IMPLEMENTED,
        awsState: STATE_NOT_IMPLEMENTED,
        gcpState: STATE_NOT_IMPLEMENTED,
      },
      {
        jobId: '',
        username: 'another@mozilla.com',
        ssoState: STATE_NOT_MODIFIED,
        gsuiteState: STATE_NOT_IMPLEMENTED,
        slackState: STATE_NOT_IMPLEMENTED,
        awsState: STATE_NOT_IMPLEMENTED,
        gcpState: STATE_NOT_IMPLEMENTED,
      },
    ]
  }),
  methods: {
    finishedUpdating(jobId) {
      const finished = (state) => state !== STATE_NOT_MODIFIED

      const job = this.userStates.find((state) => state.jobId === jobId)

      return (typeof job !== 'undefined') &&
        finished(job.ssoState) &&
        finished(job.gsuiteState) &&
        finished(job.slackState) &&
        finished(job.awsState) &&
        finished(job.gcpState)
    },
    representation(state) {
      return STATE_REPRESENTATIONS[state]
    },
  },
  mounted() {
    this.$root.$on('TerminateJobCreated', (username, jsonData) => {
      this.userStates.push({
        jobId: jsonData['jobId'],
        username: username,
        ssoState: STATE_REPRESENTATIONS[STATE_NOT_MODIFIED],
        gsuiteState: STATE_NOT_IMPLEMENTED,
        slackState: STATE_NOT_IMPLEMENTED,
        awsState: STATE_NOT_IMPLEMENTED,
        gcpState: STATE_NOT_IMPLEMENTED,
      })

      const intervalId = setInterval(() => {
        if (this.finishedUpdating(jsonData['jobId'])) {
          clearInterval(intervalId)
        } else {
          this.$root.$emit('RequestStatusUpdate', jsonData['jobId'])
        }
      }, STATUS_UPDATE_INTERVAL)
    })
  }
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
  },
  mounted() {
    this.$root.$on('TerminateRequestSent', (username) => {
      fetch(TERMINATE_ENDPT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username,
        }),
      })
      .then((response) => response.json())
      .then((data) => this.$root.$emit('TerminateJobCreated', username, data))
    })
  },
}

const application = new Vue({
  el: '#application',
  components: {
    Application,
  }
})

//(function () {
//  const TERMINATE_ENDPT = '/terminate'
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

const TERMINATE_ENDPT = '/terminate'
const STATUS_ENDPT = '/status'
const STATUS_UPDATE_INTERVAL = 500


const RP_SSO = 'sso'
const RP_GSUITE = 'gsuite'
const RP_SLACK = 'slack'
const RP_AWS = 'aws'
const RP_GCP = 'gcp'

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
        ssoState: STATE_NOT_MODIFIED,
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

    this.$root.$on('ApplyStatusUpdate', (jobId, jsonData) => {
      const job = this.userStates.find((state) => state.jobId === jobId)

      if (typeof job === 'undefined') {
        console.log(`Got an update for invalid job ${jobId}`)
        return
      }

      for (const result of jsonData['results']) {
        if (result['affectedRP'] === RP_SSO) {
          job.ssoState = result['currentState']
        } else if (result['affectedRP'] === RP_GSUITE) {
          job.gsuiteState = result['currentState']
        } else if (result['affectedRP'] === RP_SLACK) {
          job.slackState = result['currentState']
        } else if (result['affectedRP'] === RP_AWS) {
          job.awsState = result['currentState']
        } else if (result['affectedRP'] === RP_GCP) {
          job.gcpState = result['currentState']
        }
      }

      // TODO : write outputs
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

    this.$root.$on('RequestStatusUpdate', (jobId) => {
      fetch(`${STATUS_ENDPT}?jobId=${jobId}`)
      .then((response) => response.json())
      .then((data) => this.$root.$emit('ApplyStatusUpdate', jobId, data))
    })
  },
}

const application = new Vue({
  el: '#application',
  components: {
    Application,
  }
})

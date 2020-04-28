const TERMINATE_ENDPT = '/terminate'
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
    /* States take the following shape:
     * {
     *   username: string,
     *   ssoState: string, // One of STATE_*
     *   gsuiteState: string,
     *   slackState: string,
     *   awsState: string,
     *   gcpState: string,
     * }
     */
    userStates: [],
  }),
  methods: {
    representation(state) {
      return STATE_REPRESENTATIONS[state]
    },
  },
  mounted() {
    this.$root.$on('TerminationComplete', (username, jsonData) => {
      let job = {
        username: username,
        ssoState: STATE_NOT_MODIFIED,
        gsuiteState: STATE_NOT_MODIFIED,
        slackState: STATE_NOT_MODIFIED,
        awsState: STATE_NOT_MODIFIED,
        gcpState: STATE_NOT_MODIFIED,
      }

      const error = jsonData['error']

      if (typeof error !== 'undefined' && error !== null) {
        this.$root.$emit('GotOutput', {error})
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

        if (result['output'] !== null) {
          this.$root.$emit('GotOutput', {'output': result['output']})
        }
        if (result['error'] !== null) {
          this.$root.$emit('GotOutput', {'error': result['error']})
        }
      }

      this.userStates.push(job)
    })
  }
}

const StatusMessageList = {
  name: 'StatusMessageList',
  template: `
    <div>
      <h2>Outputs</h2>
      <ul id="outputs">
        <li v-for="error in errors" class="error">
          {{ error }}
        </li>
        <li v-for="output in outputs" class="output">
          {{ output }}
        </li>
      </ul>
    </div>
  `,
  data: () => ({
    outputs: [],
    errors: [],
  }),
  mounted() {
    this.$root.$on('GotOutput', (output) => {
      const out = output['output']
      const err = output['error']

      if (typeof out !== 'undefined') {
        this.outputs.push(out)
      }
      if (typeof err !== 'undefined') {
        this.errors.push(err)
      }
    })
  },
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
      .then((data) => this.$root.$emit('TerminationComplete', username, data))
    })
  },
}

const application = new Vue({
  el: '#application',
  components: {
    Application,
  }
})

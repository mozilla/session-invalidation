(function () {
  const TERMINATE_ENDPT = '/terminate'

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


  terminateButton.addEventListener('click', function (evt) {
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
    })
  })
})()

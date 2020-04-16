(function () {
  const terminateEndpt = '/terminate'

  const usernameInput = document.getElementById('username')

  const terminateButton = document.getElementById('terminate')

  const outputsList = document.getElementById('outputs')

  terminateButton.addEventListener('click', function (evt) {
    fetch(terminateEndpt, {
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

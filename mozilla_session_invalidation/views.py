from flask import render_template, request

from mozilla_session_invalidation import app


@app.route('/')
def index():
    app.logger.warning('sample message')
    return render_template('index.html')


@app.route('/terminate', methods=['POST'])
def terminate():
    app.logger.warning('Terminate received: {}'.format(request.json))
    return {'error': None}

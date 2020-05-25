import json


INDEX = '''<doctype HTML>
<html>
    <head>
        <title>Session Invalidation</title>
    </head>
    <body>
        <h1>Mozilla Session Invalidation</h1>
        <p>
            Hello, world!
        </p>
    </body>
</html>
'''

def index(event, context):
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': INDEX,
    }


def terminate(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'error': None,
            'results': [],
        }),
    }

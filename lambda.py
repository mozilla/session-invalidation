import json
import os
import sys

if 'LAMBDA_TASK_ROOT' in os.environ:
    sys.path.append(f"{os.environ['LAMBDA_TASK_ROOT']}/lib")
else:
    sys.path.append('lib')

import boto3


STATIC_CONTENT_BUCKET_NAME = 'session-invalidation-static-content'

ERROR_PAGE = '''<doctype HTML>
<html>
    <head>
        <title>Session Invalidation Error</title>
    </head>
    <body>
        <h1>Error</h1>
        <p>{0}</p>
    </body>
</html>
'''


def static_content(filename):
    s3 = boto3.resource('s3')
    static_content = s3.Bucket(STATIC_CONTENT_BUCKET_NAME)

    file_path = f'/tmp/{filename}'

    if not os.path.isfile(file_path):
        with open(file_path, 'wb') as f:
            static_content.download_fileobj(filename, f)

    with open(file_path, 'rb') as f:
        return f.read()


def index(event, context):
    try:
        index_page = static_content('index.html')
    except Exception as ex:
        index_page = ERROR_PAGE.format(ex)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/html',
        },
        'body': index_page,
    }


def static(event, context):
    filename = event.get('pathParameters', {}).get('filename')

    error_404 = {
        'statusCode': 404,
        'body': f'{filename} not found',
    }

    if filename is None or '.' not in filename:
        return error_404

    try:
        content = static_content(filename)
    except Exception as ex:
        return {
            'statusCode': 404,
            'body': str(ex),
        }

    ext = filename.split('.')[-1]

    content_types = {
        'css': 'text/css',
        'js': 'application/javascript',
    }

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': content_types[ext],
        },
        'body': content,
    }


def terminate(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps({
            'error': None,
            'results': [],
        }),
    }


if  __name__ == '__main__':
    print(static({'pathParameters': {'filename': 'styles.css'}}, ''))

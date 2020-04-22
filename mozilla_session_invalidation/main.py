import os

from mozilla_session_invalidation import app


def main():
    if not app.debug:
        import logging
        from logging.handlers import TimedRotatingFileHandler
        # https://docs.python.org/3.6/library/logging.handlers.html#timedrotatingfilehandler
        file_handler = TimedRotatingFileHandler(os.path.join(app.config['LOG_DIR'], 'mozilla_session_invalidation.log'), 'midnight')
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(logging.Formatter('<%(asctime)s> <%(levelname)s> %(message)s'))
        app.logger.addHandler(file_handler)

    import mozilla_session_invalidation.views

    app.secret_key = os.environ['SECRET_KEY']

    app.run()


if __name__ == '__main__':
    main()

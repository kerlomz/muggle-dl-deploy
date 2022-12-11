#!/usr/bin/env python3
# -*- coding:utf-8 -*-


def serve():
    from muggle.config import cli_args, SYSTEM

    import logging
    import uvicorn.server
    from muggle.logger import logger
    from muggle.fastapi_app import app

    def info(x, *args, **kwargs):
        return logger.info(x % args, **kwargs)

    logging.getLogger('uvicorn.error').info = info
    if SYSTEM == 'Windows':
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config['disable_existing_loggers'] = True
        uvicorn.run(app, host=cli_args.host, port=cli_args.port, log_level='info', access_log=False)
    else:
        from muggle.server.gunicorn_server import GunicornServer
        logging.getLogger('gunicorn.error').info = info
        GunicornServer(app).run()


if __name__ == '__main__':
    serve()


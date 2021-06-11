workers = 8
threads = 2

bind = '0.0.0.0:5000'
daemon = 'false'

worker_class = 'gevent'

worker_connections = 2000

pidfile = '/var/run/gunicorn.pid'

accesslog = 'logs/access.log'
errorlog = 'logs/debug.log'

loglevel = 'info'


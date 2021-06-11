#pip3 install gunicorn gevent

export FLASK_ENV=production

gunicorn -w 8 -t 20 -b 0.0.0.0:5000 -k gevent --worker-tmp-dir /tmp flask-omnibus:app

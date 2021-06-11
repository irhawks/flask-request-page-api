FROM python:3-alpine
ADD . /opt/requests
WORKDIR /opt/requests
RUN pip3 install -r /opt/requests/requirements.txt

ENTRYPOINT ["python3", "flask-omnibus.py"]

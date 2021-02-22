FROM python:3.7-alpine
COPY requirements.txt /
RUN pip3 install -r /requirements.txt
COPY app/ app/
COPY run-app.sh /
CMD [ "sh", "run-app.sh" ]


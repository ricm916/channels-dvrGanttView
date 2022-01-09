FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY blank.gif ./
RUN pip install --no-cache-dir -r requirements.txt
COPY channels-dvr-gantt.py .
EXPOSE 80/tcp
CMD [ "python", "./channels-dvr-gantt.py" ]

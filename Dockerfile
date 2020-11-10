# In path/to/your/dev/folder/Dockerfile
# Base Image
FROM python:3.8
MAINTAINER iqbal-sysable

ENV PYTHONUNBUFFERED 1


COPY ./requirement.txt /requirement.txt
RUN pip install -r /requirement.txt


ENV PORT=8000
CMD gunicorn video_stream.wsgi:application --bind 0.0.0.0:$PORT

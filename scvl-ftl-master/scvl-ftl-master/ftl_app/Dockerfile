FROM python:3.6

ADD ./python_requirements.txt .

RUN pip install -r python_requirements.txt 

RUN mkdir -p /usr/app
WORKDIR /usr/app
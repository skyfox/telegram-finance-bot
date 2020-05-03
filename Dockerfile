FROM python:3.7.7
RUN apt-get update && apt-get -y install libleveldb-dev

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot
ADD . /usr/src/bot
RUN pip install -r requirements.txt
WORKDIR /usr/src/bot/bot
ENTRYPOINT python bot.py
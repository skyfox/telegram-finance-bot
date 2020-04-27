FROM python:3.7.7

RUN mkdir -p /usr/src/bot
WORKDIR /usr/src/bot
ADD . /usr/src/bot
RUN pip install -r requirements.txt
WORKDIR /usr/src/bot/bot
ENTRYPOINT python bot.py
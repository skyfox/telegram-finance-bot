# Python version
FROM python:3.7.7

# Creating bot folder in container
RUN mkdir -p /usr/src/bot
# Setting workdir
WORKDIR /usr/src/bot
# Copying all directory data to vot folder
ADD . /usr/src/bot
# Installing dependences 
RUN pip install -r requirements.txt
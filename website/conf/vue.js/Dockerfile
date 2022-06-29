FROM node:latest

ARG NODE_ENV
ENV NODE_ENV=${NODE_ENV}

RUN apt-get -y update && apt-get install -y git
RUN npm install -g http-server
RUN npm install -g npm@latest
RUN npm install -g @vue/cli
WORKDIR /app



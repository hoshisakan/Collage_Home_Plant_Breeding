FROM python:3.7.6

ARG PYTHONUNBUFFERED
ENV PYTHONUNBUFFERED ${PYTHONUNBUFFERED}
RUN ln -sf /usr/share/zoneinfo/Asia/Taipei /etc/localtime
WORKDIR /server
COPY requirements.txt /server/
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
# RUN pip3 install --user --upgrade aws-sam-cli
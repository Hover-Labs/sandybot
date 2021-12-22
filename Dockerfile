FROM python:3

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y git build-essential jq

RUN git clone https://github.com/wolfcw/libfaketime.git /tmp/libfaketime && cd /tmp/libfaketime && make && make install

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./main.py" ]

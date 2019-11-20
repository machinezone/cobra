FROM python:3.8.0-alpine3.10

# Install build dependencies
RUN apk add --no-cache gcc g++ musl-dev linux-headers make

# Install dependant packages
COPY requirements.txt /tmp
RUN pip install --requirement /tmp/requirements.txt

RUN apk add --no-cache libstdc++

COPY . /home/app
WORKDIR /home/app
RUN pip install .

EXPOSE 8765
CMD ["cobra", "run"]
HEALTHCHECK CMD cobra health

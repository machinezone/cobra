# Build time
FROM ubuntu:focal as build

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update

RUN apt-get -y install g++
RUN apt-get -y install libssl-dev
RUN apt-get -y install libz-dev
RUN apt-get -y install make
RUN apt-get -y install cmake
RUN apt-get -y install python

COPY . .

RUN mkdir build
WORKDIR /opt/build
RUN conan install ..
RUN cmake -GNinja ..
RUN ninja

# Runtime
FROM ubuntu:focal as runtime

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
# Runtime
RUN apt-get install -y libssl1.1
RUN apt-get install -y ca-certificates
RUN ["update-ca-certificates"]

# Debugging
RUN apt-get install -y strace
RUN apt-get install -y procps
RUN apt-get install -y htop

RUN adduser --disabled-password --gecos '' app
COPY --chown=app:app --from=build /usr/local/bin/ws /usr/local/bin/ws
RUN chmod +x /usr/local/bin/ws
RUN ldd /usr/local/bin/ws

# Now run in usermode
USER app
WORKDIR /home/app

COPY --chown=app:app ws/snake/appsConfig.json .
COPY --chown=app:app ws/cobraMetricsSample.json .

ENTRYPOINT ["ws"]
CMD ["--help"]

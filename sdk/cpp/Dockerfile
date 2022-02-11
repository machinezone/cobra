# Build time
# focal == ubuntu 2020.04
FROM ubuntu:focal as build

RUN apt update

RUN apt-get -y install g++
RUN apt-get -y install ninja-build
RUN apt-get -y install cmake
RUN apt-get -y install python3-dev
RUN apt-get -y install python3-pip
RUN pip3 install conan==1.43.0  # Match the version defined in Makefile deps:

COPY . /opt
WORKDIR /opt

RUN mkdir build
WORKDIR /opt/build
# We need to specify the compiler here or we'll have weird linking errors
RUN conan install -s compiler=gcc -s compiler.version=9 -s compiler.libcxx=libstdc++11 --build=missing ..
RUN cmake -GNinja -DCMAKE_BUILD_TYPE=MinSizeRel ..
RUN ninja install

# Runtime
FROM ubuntu:focal as runtime

RUN apt update
# Runtime
RUN apt-get install -y python3
RUN apt-get install -y python3-dev      # necessary to include libpython
RUN apt-get install -y ca-certificates
RUN ["update-ca-certificates"]

# Debugging
RUN apt-get install -y strace
RUN apt-get install -y procps
RUN apt-get install -y htop

RUN adduser --disabled-password --gecos '' app
COPY --chown=app:app --from=build /usr/local/bin/cobra_cli /usr/local/bin/cobra_cli
RUN chmod +x /usr/local/bin/cobra_cli
RUN ldd /usr/local/bin/cobra_cli

# Now run in usermode
USER app
WORKDIR /home/app

COPY --chown=app:app cli/cobraMetricsSample.json .

ENTRYPOINT ["cobra_cli"]
CMD ["--help"]

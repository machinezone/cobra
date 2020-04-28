# Build stage
FROM bitnami/python:latest as build
env PIP_DOWNLOAD_CACHE=/opt/pip_cache

ENV DEBIAN_FRONTEND noninteractive

# Install build dependencies
RUN apt-get -y install g++ make

# Install dependant packages
RUN pip install --cache-dir=/opt/pip_cache --user uvloop==0.14.0
COPY requirements.txt /tmp
RUN pip install --cache-dir=/opt/pip_cache --user --requirement /tmp/requirements.txt

# Runtime stage
FROM bitnami/python:latest as runtime
RUN adduser --disabled-password --gecos '' app

COPY --chown=app:app --from=build /opt/pip_cache /opt/pip_cache

RUN ln -sf /home/app/.local/bin/cobra /usr/bin/cobra && \
	ln -sf /home/app/.local/bin/rcc /usr/bin/rcc && \
	ln -sf /home/app/.local/bin/bavarde /usr/bin/bavarde

COPY --chown=app:app . /home/app
USER app

WORKDIR /home/app
RUN pip install --cache-dir=/opt/pip_cache --user -e .

EXPOSE 8765
CMD ["cobra", "run"]
HEALTHCHECK CMD cobra health

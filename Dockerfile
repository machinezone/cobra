# Build stage
FROM python:3.8.0-alpine3.10 as build
env PIP_DOWNLOAD_CACHE=/opt/pip_cache

# Install build dependencies
RUN apk add --no-cache gcc musl-dev linux-headers make

# Install dependant packages
COPY requirements.txt /tmp
RUN pip install --cache-dir=/opt/pip_cache --user --requirement /tmp/requirements.txt

# Runtime stage
FROM python:3.8.0b4-alpine3.10 as runtime
RUN addgroup -S app && adduser -S -G app app

COPY --chown=app:app --from=build /opt/pip_cache /opt/pip_cache

RUN ln -sf /home/app/.local/bin/cobra /usr/bin/cobra
COPY --chown=app:app . /home/app
USER app
WORKDIR /home/app
RUN pip install --cache-dir=/opt/pip_cache --user -e .

EXPOSE 8765
CMD ["cobra", "run"]
HEALTHCHECK CMD cobra health

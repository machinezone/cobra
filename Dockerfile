FROM python:3.9.2-alpine3.13

COPY requirements.txt /tmp

# Install build dependencies
RUN apk add --no-cache g++ musl-dev linux-headers make && \
    pip install --requirement /tmp/requirements.txt && \
    apk del g++ musl-dev linux-headers make

RUN addgroup -S app && adduser -S -G app app
RUN apk add --no-cache zsh redis libstdc++

RUN ln -sf /home/app/.local/bin/cobra /usr/bin/cobra

COPY --chown=app:app . /home/app
COPY --chown=app:app .zshrc /home/app/.zshrc
USER app

WORKDIR /home/app
RUN pip install --user -e .

EXPOSE 8765
CMD ["cobra", "run"]
HEALTHCHECK CMD cobra health

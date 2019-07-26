FROM python:3.7.3-alpine3.10

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt /tmp
RUN apk add --no-cache gcc musl-dev linux-headers make && \
    pip install --no-cache-dir --requirement /tmp/requirements.txt && \
    apk del --no-cache gcc musl-dev linux-headers make

RUN ln -sf /home/app/.local/bin/cobra /usr/bin/cobra
RUN addgroup -S app && adduser -S -G app app 

COPY --chown=app:app . .
USER app
RUN pip install --user -e .

EXPOSE 8765
CMD ["cobra", "run"]
HEALTHCHECK CMD cobra health

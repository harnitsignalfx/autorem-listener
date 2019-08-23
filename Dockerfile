FROM python:3.5-alpine

COPY requirements.txt ./

RUN apk --update --no-cache add curl

RUN pip install --no-cache-dir -r requirements.txt

COPY server.py ./

COPY writeFile.py ./

CMD python server.py

HEALTHCHECK --interval=10s --timeout=3s \
  CMD curl -f http://localhost:6000/healthz || exit 1

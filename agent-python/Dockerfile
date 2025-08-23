FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tini build-essential python3-dev \
  && rm -rf /var/lib/apt/lists/*

# deps ușoare, fără ML greu
RUN pip install --no-cache-dir \
    uvloop==0.19.0 \
    orjson==3.10.7 \
    aiomqtt==1.2.0 \
    tdigest==0.5.2.2

WORKDIR /app
COPY agent /app/agent
COPY tools /app/tools

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["python","-m","agent.main"]

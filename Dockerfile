FROM juholeinonen/kaldi-align@sha256:20056bf9c2af15d4f1a5c9f3567c8aeb23394ee6f01d9a395fb032a6a33ad4de as kaldi-build
ENV LANG en_US.UTF-8
# Install tini and create an unprivileged user
ADD https://github.com/krallin/tini/releases/download/v0.19.0/tini /usr/bin/tini 
RUN chmod +x /usr/bin/tini 

# Create a Python virtual environment for the dependencies
FROM python:3.8-slim as venv-build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip --no-cache-dir install -r requirements.txt

# ELG main app here
FROM python:3.8-slim 
COPY --from=kaldi-build /usr/bin/tini /usr/bin/tini
COPY --from=kaldi-build  /opt/kaldi/ /opt/kaldi/

WORKDIR  /opt/kaldi/egs/align
RUN chmod +x /usr/bin/tini
COPY --from=venv-build /opt/venv /opt/venv
COPY pipelines/align.sh aligning_with_Docker/bin/
RUN apt-get update && apt-get install perl liburi-encode-perl -y
RUN apt-get update && apt-get install g++ make automake autoconf patch bzip2 unzip wget git sox gfortran libtool subversion python2.7 zlib1g-dev -y \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*
RUN /opt/kaldi/tools/extras/install_mkl.sh
COPY app.py utils.py docker-entrypoint.sh /opt/kaldi/egs/align/

ENV PATH="/opt/venv/bin:/opt/kaldi/src/fstbin:$PATH"
ENV LD_LIBRARY_PATH="/opt/kaldi/src/base/"


ENV WORKERS=2
ENV TIMEOUT=60
ENV WORKER_CLASS=sync
ENV LOGURU_LEVEL=INFO
ENV PYTHON_PATH="/opt/venv/bin"


RUN chmod +x ./docker-entrypoint.sh
ENTRYPOINT ["./docker-entrypoint.sh"]

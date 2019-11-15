FROM ubuntu:19.10
MAINTAINER OCR-D
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8

WORKDIR /build-ocrd
COPY ocrd ./ocrd
COPY ocrd_modelfactory ./ocrd_modelfactory/
COPY ocrd_models ./ocrd_models
COPY ocrd_utils ./ocrd_utils
COPY ocrd_validators/ ./ocrd_validators
COPY Makefile .
COPY README.md .
COPY LICENSE .
RUN apt-get update && apt-get -y install --no-install-recommends \
    ca-certificates \
    python3-dev \
    python3-pip \
    make \
    wget \
    sudo \
    git \
    libglib2.0-0 \
    python3 \
    python3-pip
    libglib2.0.0 \
    && pip3 install --upgrade pip setuptools \
    && make install \
    && rm -rf /build-ocrd

WORKDIR /data

CMD ["/usr/local/bin/ocrd", "--help"]

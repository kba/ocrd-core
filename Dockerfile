FROM ubuntu:19.10
MAINTAINER OCR-D
ENV DEBIAN_FRONTEND noninteractive
ENV PYTHONIOENCODING utf8
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

WORKDIR /build-ocrd
COPY ocrd ./ocrd
COPY ocrd_modelfactory ./ocrd_modelfactory/
COPY ocrd_models ./ocrd_models
COPY ocrd_utils ./ocrd_utils
COPY ocrd_validators/ ./ocrd_validators
COPY Makefile .
COPY README.md .
COPY LICENSE .
RUN apt-get update && \
    apt-get -y install --no-install-recommends \
    ca-certificates \
    make \
    sudo \
    git \
    libglib2.0-0 \
    python3 \
    python3-pip
RUN pip3 install --upgrade pip setuptools
RUN make install

ENTRYPOINT ["/usr/local/bin/ocrd"]

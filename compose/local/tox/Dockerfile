FROM quantra2112/ci-images-arm

USER root

RUN apt update && apt install -y libpq-dev build-essential libjpeg-dev libpng-dev libwebp-dev && apt install --reinstall python3-pkg-resources python3-setuptools

ARG BUILD_ENVIRONMENT=local
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

# copy application code to WORKDIR
COPY . ${APP_HOME}

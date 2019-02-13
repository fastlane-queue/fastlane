FROM python:3.7.2-slim-stretch

RUN apt-get update -y && apt-get install -y --no-install-recommends curl=7.52.1-5+deb9u9 make=4.1-9.1 \
                                                 software-properties-common=0.96.20.2-1 \
                                                 build-essential=12.3 \
                                                 git=1:2.11.0-3+deb9u4 \
                                                 wget \
                      && apt-get clean \
                      && rm -rf /var/lib/apt/lists/*

ENV HOME "/root"
RUN mkdir -p ${HOME}
RUN bash -c 'curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python'
ENV PATH="${HOME}/.poetry/bin:${PATH}"
RUN poetry --version

# Dockerize - https://github.com/jwilder/dockerize
ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz


# Configure VEnv
ENV WORKON_HOME "${HOME}/.virtualenvs"
RUN mkdir -p "${WORKON_HOME}"
RUN pip install virtualenvwrapper
RUN /bin/bash -c "source virtualenvwrapper.sh && mkvirtualenv fastlane"
RUN chown -R root:root ${WORKON_HOME}
ENV VENV_PATH "${WORKON_HOME}/fastlane/bin"
ENV VIRTUAL_ENV ${WORKON_HOME}/fastlane
ENV PATH="${WORKON_HOME}/fastlane/bin:${PATH}"
# End VEnv Config

RUN pip install honcho==1.0.1
RUN mkdir -p /app
WORKDIR /app
COPY . /app
RUN poetry install --no-dev
RUN echo "Verifying fastlane version..." && poetry run fastlane version

ENV REDIS_URL "redis://redis:6379/0"
ENV DOCKER_HOSTS "[{\"match\": \"\", \"hosts\": [\"localhost:2376\"], \"maxRunning\":2}]"
ENV MONGODB_CONFIG "{\"host\": \"mongodb://mongo:27017/fastlane\", \"db\": \"fastlane\", \"serverSelectionTimeoutMS\": 100, \"connect\": false}"
ENV MONGODB_HOST="mongo:27017"
ENV REDIS_HOST="redis:6379"

# If you don't want to wait use `CMD honcho --no-colour start`
CMD dockerize -wait tcp://$MONGODB_HOST -wait tcp://$REDIS_HOST honcho --no-colour start

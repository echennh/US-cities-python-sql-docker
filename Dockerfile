# build
FROM python:3.11-slim AS builder

# System libs required by mysqlclient / mysql-connector-python
RUN apt-get update && apt-get install -y --no-install-recommends \
        default-libmysqlclient-dev gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# the build context directory is the directory on the host machine where docker will get the files to build the image
# the build context directory is not necessarily where the Dockerfile is located'


# makes a directory app and sets it as the working directory
WORKDIR /app
# the following command copies the requirements.txt from my US-cities-python-sql-docker folder to the app directory
COPY requirements.txt .
RUN python -m venv /opt/venv  && /opt/venv/bin/pip install --upgrade pip && /opt/venv/bin/pip install -r requirements.txt
COPY src/ ./src
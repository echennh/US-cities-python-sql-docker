# Stage 1: build - install build tools, compile wheels, create the virtual environment
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
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install -r requirements.txt

# code is present *in this stage*
COPY src/ src/

# Stage 2: run - begin from a fresh slim base, copying only the virtual environment and my code, leaving the bulky compile layers behind
FROM python:3.11-slim

# Tell Cpython to not create __pycache__/*.pyc files, which keeps layers smaller and avoids permissions noise when running as non-root
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
# force stdout/stderr to be line buffered (unbuffered) so that my app's print() and logging appear instantly in docker logs, even if the process crashes right after writing

# copy from the already-created filesystem of the builder stage rather than the build context
# so I can guarantee that the runtime code is the exact code that was used when dependencies were installed (for reproducibility)
# this is build-cache-friendly
WORKDIR /app
# ⬇ bring both venv and code across. Copying the virtual env from builder keeps runtime smaller
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/src /app/src

# can't launch python here because it interferes with debugging

CMD []
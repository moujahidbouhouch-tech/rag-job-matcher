FROM n8nio/n8n:latest

USER root

# Install Python, pip, and Chromium dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    chromium \
    chromium-chromedriver \
    && ln -sf /usr/bin/python3 /usr/bin/python

# Copy requirements file
COPY requirements.txt /tmp/requirements.txt

# Install Python packages from requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages \
    -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

USER node

FROM n8nio/n8n:latest

USER root

# Install Python and dependencies (Alpine base)
RUN apk add --no-cache \
    python3 \
    py3-pip \
    chromium \
    chromium-chromedriver

USER node
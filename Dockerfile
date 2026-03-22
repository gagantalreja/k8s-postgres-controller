FROM python:3.12-slim

# Terraform version
ARG TERRAFORM_VERSION=1.10.5
COPY ./controller.py /app/controller.py
COPY ./requirements.txt /app/requirements.txt
COPY ./terraform /app/terraform

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Terraform
RUN curl -fsSL https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip \
    -o terraform.zip \
    && unzip terraform.zip \
    && mv terraform /usr/local/bin/terraform \
    && rm terraform.zip

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

CMD ["python", "controller.py"]
FROM --platform=linux/amd64 python:3.12.7

WORKDIR /code

# Environment config
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOCKER_CONTENT_TRUST=1 \
    APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn \
    PATH="$PATH:/opt/mssql-tools/bin"

# Install ODBC drivers and dependencies
RUN apt-get update && \
    apt-get install -y curl gnupg apt-transport-https unixodbc unixodbc-dev libgssapi-krb5-2 && \
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 mssql-tools && \
    rm -rf /var/lib/apt/lists/*

# Install Python packages
COPY ./requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ./src ./src

CMD ["python", "./src/main.py"]

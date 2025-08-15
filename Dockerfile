FROM --platform=linux/amd64 python:3.12.7
RUN pip install --upgrade pip

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

ENV PYTHONUNBUFFERED=1
EXPOSE 80


CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]


# docker build -t crm-document-organizer .
# docker tag crm-document-organizer us-west2-docker.pkg.dev/polling-apps/core/crm-document-organizer:lastest
# docker push us-west2-docker.pkg.dev/polling-apps/core/crm-document-organizer:lastest

FROM --platform=linux/amd64 python:3.12.7
RUN pip install --upgrade pip

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src

ENV PYTHONUNBUFFERED=1
EXPOSE 80


CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "80"]

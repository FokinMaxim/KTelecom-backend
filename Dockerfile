FROM python:3.12.3

WORKDIR /

ENV PYTHONUNBUFFERED 1

RUN apt update

COPY requirements.txt .

RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.app.apps:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

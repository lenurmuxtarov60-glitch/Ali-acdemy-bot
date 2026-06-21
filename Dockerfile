FROM python:3.11-slim

WORKDIR /app

COPY requirements-prod.txt requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install -r requirements-prod.txt

COPY . .

CMD ["python", "run.py"]

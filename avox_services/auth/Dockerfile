FROM python:3.12-slim



COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /auth

WORKDIR /

CMD ["uvicorn", "auth.app.main:app", "--host", "0.0.0.0", "--port", "8001"]

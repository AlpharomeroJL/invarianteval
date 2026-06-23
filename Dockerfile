FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY invarianteval ./invarianteval
RUN pip install -e .

# Use slim official Python image
FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing bytecode and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_INDEX_URL=https://pypi.org/simple

# Install requirements
COPY requirements-runtime.txt requirements.txt
# This backend runs STQGCN on CPU; avoid pulling the much larger CUDA build.
RUN pip install --no-cache-dir --timeout 180 --retries 5 --index-url https://download.pytorch.org/whl/cpu torch
RUN pip install --no-cache-dir --timeout 180 --retries 5 --index-url https://pypi.org/simple -r requirements.txt

# Copy application source code
COPY . .

# Expose backend port
EXPOSE 8000

# Run FastAPI using uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

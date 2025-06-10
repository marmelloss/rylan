FROM python:3.10

WORKDIR /app

# Copy all files (adjust as needed)
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Verify the files were copied correctly
RUN ls -la /app && ls -la /app/templates

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

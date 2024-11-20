FROM python:3.9

WORKDIR /code

# Add missing import statement
RUN apt-get update && apt-get install -y git

# Install Python dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Install ptvsd for remote debugging
RUN pip install ptvsd

# Any more dependencies
RUN pip install python-multipart aiofiles uvicorn

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    poppler-utils \
    tesseract-ocr \
    libmagic-dev

# Create and set permissions for cache and nltk_data directories
RUN mkdir -p /.cache && chmod 777 /.cache
RUN mkdir -p /nltk_data && chmod -R 777 /nltk_data

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
#CMD ["python", "main.py"]  # Assuming your main application file is named "main.py"

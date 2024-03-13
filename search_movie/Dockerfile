FROM python:3.9

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

# Set the environment variable PORT to 8501
ENV PORT 8501

# Start the Streamlit app and listen on port 8501
CMD ["streamlit", "run", "--server.port", "8501", "app.py"]

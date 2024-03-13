FROM python:3.9

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

COPY . /app

# Set the environment variable PORT to 8080
ENV PORT 8080

# Start the Streamlit app and listen on port 8080
CMD ["streamlit", "run", "--server.port", "8080", "app.py"]


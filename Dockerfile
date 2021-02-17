FROM python:3.8-slim-buster

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy app code
WORKDIR /opt/app
COPY run.py .
COPY /tradingBot ./tradingBot

CMD python ./run.py

FROM zauberzeug/nicegui:2.4.0

LABEL org.opencontainers.image.source=https://github.com/riccardomc/stationator
LABEL org.opencontainers.image.description="A simple application to get train times between Amsterdam and Den Haag"

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN rm -rf /app/*
COPY *.py /app

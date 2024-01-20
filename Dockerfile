FROM python:3.10-slim-bookworm

WORKDIR /service

COPY requirements/prod.txt requirements/prod.txt 

RUN pip install -r requirements/prod.txt 

COPY njordr njordr

CMD ["python3", "njordr/service/main.py"]

FROM python:3.10-slim-bookworm as requirements-stage

RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock* /tmp/

WORKDIR /tmp

RUN poetry export -f requirements.txt \
                  --output requirements.txt \
                  --without-hashes


FROM python:3.10-slim-bookworm

WORKDIR /service

COPY --from=requirements-stage /tmp/requirements.txt /service/requirements.txt

RUN pip install -r requirements.txt

COPY njordr_service njordr

CMD ["python3", "njordr/main.py"]

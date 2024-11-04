FROM grey0ne/dev-environment:0.7.1

ENV PYTHONUNBUFFERED=1
ENV POETRY_VIRTUALENVS_CREATE=false

WORKDIR /app

COPY backend/pyproject.toml /app/
RUN poetry install

RUN chown -R greyone:greyone /app

ENV NODE_ENV=development

WORKDIR /app/src

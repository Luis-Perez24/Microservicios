# services/administracion/Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    RESERVAS_URL=http://reservas:8000

WORKDIR /srv

COPY services/administracion/requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt \
    && groupadd --system app \
    && useradd --system --gid app --no-create-home app

COPY shared/__init__.py shared/reservas_client.py /srv/shared/
COPY services/__init__.py /srv/services/__init__.py
COPY services/administracion/__init__.py /srv/services/administracion/__init__.py
COPY services/administracion/app/*.py /srv/services/administracion/app/

USER app
EXPOSE 8000

CMD ["uvicorn", "services.administracion.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

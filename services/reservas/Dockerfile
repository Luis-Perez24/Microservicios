FROM python:3.12-slim

WORKDIR /srv

COPY services/reservas/requirements.txt /srv/services/reservas/requirements.txt
RUN pip install --no-cache-dir -r /srv/services/reservas/requirements.txt

COPY . /srv

EXPOSE 8000

CMD ["uvicorn", "services.reservas.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
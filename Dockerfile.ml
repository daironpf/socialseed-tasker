FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN python -m pip install --upgrade pip && pip install -e . uvicorn pydantic
EXPOSE 8090
CMD ["uvicorn", "socialseed_tasker.ml.server:app", "--host", "0.0.0.0", "--port", "8090"]

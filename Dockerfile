# Production image (used by Render; runs anywhere Docker runs).
FROM python:3.12-slim

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    MODEL_CACHE_DIR=/home/user/models
WORKDIR /home/user/app

COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Bake the embedding model into the image so a cold start doesn't download it.
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2', cache_dir='/home/user/models')"

COPY --chown=user . .
EXPOSE 8000
# Render (and most hosts) pass the port in $PORT.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

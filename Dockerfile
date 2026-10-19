# Image for Hugging Face Spaces (Docker SDK). Also runs anywhere Docker runs.
FROM python:3.12-slim

# Spaces run containers as user 1000.
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1
WORKDIR /home/user/app

# CPU-only PyTorch first: the default Linux wheel bundles CUDA and is several GB.
RUN pip install --no-cache-dir --user torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Download the embedding model at build time so startup doesn't need the internet.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY --chown=user . .
EXPOSE 7860
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]

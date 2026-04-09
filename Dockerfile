# --- Stage 1: Build Frontend ---
FROM node:18-slim AS frontend-builder
WORKDIR /build

# Cache dependencies
COPY frontend/package*.json ./
RUN npm install

# Build frontend
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Final Image ---
FROM python:3.10-slim

# Create user for Hugging Face compatibility
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# Cache backend dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy essential project files
COPY --chown=user . $HOME/app/

# Copy built frontend to the static directory
COPY --chown=user --from=frontend-builder /build/out $HOME/app/static

EXPOSE 7860

# Use python -m uvicorn for direct execution
CMD ["python3", "-m", "uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "info"]

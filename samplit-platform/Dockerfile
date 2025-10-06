# Dockerfile

# Build stage - compila código sensible
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install cython numpy scipy

# Copy solo el engine
COPY engine/ ./engine/

# Compile core modules to .so (binary)
RUN python -m cython engine/core/allocators/*.py \
    && python setup.py build_ext --inplace

# Runtime stage - solo binarios
FROM python:3.11-slim

WORKDIR /app

# Copy solo lo necesario
COPY --from=builder /app/engine/*.so ./engine/
COPY orchestration-layer/ ./orchestration-layer/
COPY public-api/ ./public-api/
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# No source code in final image!
# Solo .so compilados que no son legibles

CMD ["uvicorn", "public-api.main:app", "--host", "0.0.0.0"]

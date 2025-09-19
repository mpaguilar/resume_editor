# Stage 1: Build the dependencies
FROM python:3.12-slim as builder

# Set environment variables for Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install build dependencies
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Install uv, the package manager used by the project
RUN pip install uv

WORKDIR /app

# Copy the dependency definition file
COPY pyproject.toml ./

# Install non-dev dependencies from pyproject.toml using uv
RUN uv pip compile pyproject.toml -o requirements.txt && \
    uv pip sync --system requirements.txt

# Install gunicorn in the build stage
RUN uv pip install --system gunicorn


# Stage 2: Create the final runtime image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a non-root user and group to run the application securely
RUN addgroup --system app && adduser --system --group app

# Copy the installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
# Copy executables from the builder stage
COPY --from=builder /usr/local/bin /usr/local/bin

# Set the working directory in the final image
WORKDIR /app

# Copy the application source code and set ownership to the non-root user
COPY --chown=app:app ./resume_editor ./resume_editor

# Switch to the non-root user
USER app

# Expose the port the application will run on
EXPOSE 8000

# Command to run the FastAPI application using gunicorn with uvicorn workers
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "resume_editor.app.main:create_app()"]

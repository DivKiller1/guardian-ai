FROM python:3.9-slim

WORKDIR /app

# Install PyTorch and dependencies
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
RUN pip install flask requests numpy pandas psutil prometheus-client

# Copy all Python files
COPY *.py ./
COPY pytorch_models.py ./

# Create directories
RUN mkdir -p /app/logs /app/models /app/data

EXPOSE 5000 5500

CMD ["python", "ai_detection_service.py"]

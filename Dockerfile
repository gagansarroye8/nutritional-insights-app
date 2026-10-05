FROM python:3.12-slim

# Make Python logs appear immediately and force Matplotlib to render without a GUI.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

WORKDIR /app

# Install dependencies in a separate layer so Docker can reuse the layer when
# only the application code changes.
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY data_analysis.py All_Diets.csv ./

# The analysis script creates this directory when needed. Declaring it here
# makes the intended output location clear.
RUN mkdir -p /app/outputs

CMD ["python", "data_analysis.py", "--input", "/app/All_Diets.csv", "--output", "/app/outputs"]

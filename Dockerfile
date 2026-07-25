FROM python:3.13.5-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH \
	PYTHONPATH=$HOME/app:$PYTHONPATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Try and run pip command after setting the user with `USER user` to avoid permission issues with Python
RUN pip install --no-cache-dir --upgrade pip

# Copy the current directory contents into the container at $HOME/app setting the owner to the user
COPY --chown=user requirements.txt ./
COPY --chown=user config.ini ./
COPY --chown=user streamlit_app.py ./
COPY --chown=user main.py ./
COPY --chown=user src/ ./src/
COPY --chown=user examples/ ./examples/

RUN pip install -r requirements.txt

# Create necessary directories
RUN mkdir -p logs

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
FROM python:3.10.6
WORKDIR /NimbleChallenge
COPY server.py .
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y libgl1-mesa-glx
CMD ["python3", "server.py"]

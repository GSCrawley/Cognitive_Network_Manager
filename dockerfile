FROM python:3.9-slim
RUN pip3 install --upgrade pip
WORKDIR /CNM
COPY . /CNM
COPY . /requirements.txt
RUN pip --no-cache-dir install -r requirements.txt
EXPOSE 6000
COPY . /python_proof
CMD ["python3", "manager.py"]
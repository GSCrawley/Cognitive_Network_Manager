FROM python:3.8-slim
RUN pip3 install --upgrade pip
WORKDIR /CNM
COPY . /CNM
COPY . /requirements.txt
RUN pip --no-cache-dir install -r requirements.txt
EXPOSE 8080
ENV PORT 8080
CMD ["python3", "main.py"]
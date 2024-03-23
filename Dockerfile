FROM pytorch/pytorch:latest

COPY . .

RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python3", "main.py"]
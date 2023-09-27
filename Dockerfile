FROM python:slim

RUN useradd microblog 

WORKDIR /home/microblog

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate"
RUN pip install -r requirements.txt
RUN pip install gunicorn pymongo cryptography

COPY app app
COPY microblog.py config.py ./

ENV FLASK_APP microblog.py
ENV MONGODB_URI="mongodb://mongo:27017/microblog"

EXPOSE 8000

CMD ["gunicorn", "-b 0.0.0.0:8000", "microblog:app"]

# Instructions to deploy on Docker with Flask and MongoDB

## Fase 1

Instalar docker de la web oficial con wsl2

## Fase 2

Una vez instalado usamos el comando docker version para ver que se ha instalado correctamente

## Fase 3 

Crearemos el docker file para cada cosa externa que use la app, pj: Elasticsearch, comando para los correos, Base de datos.
Yo solo haré el de mongo y la app

Docker file App:
``` 
FROM python:slim

RUN useradd microblog 

WORKDIR /home/microblog

COPY requirements.txt requirements.txt
RUN python -m venv venv
RUN /bin/bash -c "source venv/bin/activate"
RUN pip install -r requirements.txt
RUN pip install gunicorn pymongo cryptography

COPY app app
COPY microblog.py config.py  __init__.py ./


ENV FLASK_APP microblog.py
ENV MONGODB_URI="mongodb://mongoserver-container:27017/microblog"


EXPOSE 8000
WORKDIR /home
CMD  ["gunicorn","-w 4","-b 0.0.0.0:8000", "microblog.
microblog:app"]
```

Docker file mongo:
``` 
FROM mongo:latest

LABEL maintainer="tu_nombre@tucorreo.com"

EXPOSE 27017

WORKDIR /data/db

CMD ["mongod"]
``` 

## Fase 4

Ejecutamos el comando docker build para ambos dockerfiles asi:

Docker file App:
``` 
docker build -t microblog:latest .
```

Docker file mongo (indicamos el archivo con -f):
``` 
docker build -t mongodb:latest -f Dockerfile-Mongo .
```

Comprobamos que se han creado correctamente con docker images

## Fase 5


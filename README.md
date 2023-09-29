# Instrucciones para desplegar en Docker con Flask y MongoBD

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
COPY microblog.py config.py ./


ENV FLASK_APP microblog.py
ENV MONGODB_URI="mongodb://mongo:27017/microblog"


EXPOSE 8000
CMD  ["gunicorn","-w 4","-b 0.0.0.0:8000", "microblog:app"]
```

Inciso, esto de aquí: ```["gunicorn","-w 4","-b 0.0.0.0:8000", "microblog:app"]``` es muy importante porque va en función de la estructura de tu proyecto


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

Creamos una network para unir ambos contenedores

```
docker network create mi-red
```

En mi caso lo llamé red

## Fase 6

Ejecutamos el comando docker run pero pasandole el nombre de la network con la imagen

Docker file App:
```
docker run -d --name microblog -p 8000:8000 --network red microblog:latest
```

Docker file Mongo:
```
docker run -d --name microblog -p 27017:27017 --network red mongodb:latest
```

## Fase 7

Por último antes de ir a localhost:8000, revisar que tenemos mongoDB encendido, y una vez comprobado tendríamos nuestra aplicación deslegada
![img.png](img.png)


# Quick start

## Prerequsites:
- Docker compose installed

1. Clone the repo
2. Make sure docker is running
3. Build and start the MySQL db only (first terminal)
```bash
docker compose up db --build
```
4. Load data into the database (second terminal) 
```bash
docker compose run --rm app \
load \
--file /data/cities.csv \
--user loader \
--pw-file /run/secrets/loader_pw
```
5. Run app queries against db (can reuse second terminal if you'd like)
```bash
docker compose run --rm app \ 
query \
--user ro --pw-stdin NH
```


# Debugging

If you want to get into the db to just run some queries and take a look at it:
```bash
docker exec -it first_db mysql -uroot -proot geodata
```

```bash
docker exec -it first_db mysql -uloader -ploaderpass geodata
```

Inspect the docker container after build:
```bash
# 1) Build **only** the "builder" stage and give it a human-friendly tag
DOCKER_BUILDKIT=1 \
docker build \
--target builder \
  -t myapp:builder \
  .

# 2) Drop into a shell that shows you the exact filesystem of that stage
docker run --rm -it myapp:builder bash

# 3) now I can run the code that my docker container would be running
/opt/venv/bin/python -m src.app --help
```

`--target builder` stages the name from my Dockerfile
`-t myapp:builder` is where I set the tag
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
python -m src.app load \
--file /data/cities.csv \
--user loader \
--pw-file /run/secrets/loader_pw
```
5. Run app queries against db (can reuse second terminal if you'd like)
```bash
docker compose run --rm app \ 
python -m src.app --user ro --pw-stdin CA Texas
```



If you want to get into the db to just run some queries and take a look at it:
```bash
docker exec -it first_db mysql -uroot -proot geodata
```

```bash
docker exec -it first_db mysql -uloader -ploaderpass geodata
```
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
python -m src.app load \
--file /data/cities.csv \
--user loader \
--pw-file /run/secrets/loader_pw
```
5. Run app queries against db (can reuse second terminal if you'd like)
This will get you the total population in cities for each state from the latest year (2018) for each state you supply (in this case, New Hampshire and Ohio), 
then also sum it to get the grand total. It also will print logs at the debug level.
```bash
docker compose run --rm app \
python -m src.app query \
--user ro --pw-stdin --states NH Ohio --debug
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


If you want to debug in Pycharm (must have Professional),
1. go to Settings -> Project -> Python Interpreter.
2. Click on "Add Interpreter" --> "On Docker Compose"
3. In the "Services" section, click "App", then "Next"
4. Select "venv" and then type in /opt/venv/bin/python. Once you hit enter, it will stil look like there is no interpreter. Click on the interpreter box again, and now you should see the new one in the dropdown -select it.
5. In your run configuration, go choose the new interpreter and apply it to your run configuration.


## Pycharm Debugger: can't open file '/opt/.pycharm_helpers/pydev/pydevd.py': [Errno 2] No such file or directory

1. Stop all your docker containers running.
2. Exit out of Pycharm. 
3. Keep pycharm closed, and run some docker cleanup:
```bash
docker container prune
```

```bash
docker image prune
```

```bash
docker builder prune
```

```bash
docker volume prune
```

```bash
docker network prune
```

```bash
docker system prune -a --volumes   # nuke ALL unused objects
```
4. Now you can open Pycharm again, and recreate the Docker compose interpeter (see directions above.)
5. Now you can run the Pycharm run configuration in debug mode.

What happened?
PyCharm had created a named Docker volume for its debugger helpers (us-cities-python-sql-docker_pycharm_helpers_PY-…) but - because of a known JetBrains bug - never copied the helper files into it, so every debug run died with “can't open file '/opt/.pycharm_helpers/pydev/pydevd.py'”.
These prune commands deleted the stale, empty helpers volume (and associated containers/networks); when you opened PyCharm again it rebuilt the Compose interpreter from scratch, this time bind-mounting or repopulating the helpers correctly, so pydevd.py was finally present and the debugger could start.

### References
https://youtrack.jetbrains.com/issue/PY-81141

https://tomwojcik.com/posts/2021-01-20/filenotfound-fragment.py-pycharm
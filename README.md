# YASMINE

YASMINE (instrumentation metadata construction tool) is a python web application developed to generate metadata XML for a seismic stations.

## Instructions for users
### Installation using Python
1. Installed Python 3.6.5+
2. Run `python -m venv env`
3. Run `source env/bin/activate`
4. Run `pip install --upgrade pip setuptools`
5. Run `pip install YASMINE-x.x.tar.gz`
6. Run `sudo yasmineapp.py syncdb upgrade heads`
7. Run `sudo yasmineapp.py runserver`
8. Visit `http://localhost`

If there is no internet connection unzip NRL (IRIS.zip) in to the application data folder "/opt/YASMINE/_media/" or "c:/YASMINE/_media/nrl/" depending on OS (Linux/Windows based).

### Installation using Docker
1. Install Docker <https://www.docker.com/products/docker-desktop>
2. Run `docker-compose up` to download, build and deploy docker container
3. Visit `http://localhost`

## Instructions for developers
1. To develop frontend, please go to `frontend` folder and see `README.md` file
2. To develop backend, please go to `backend` folder and see `README.md` file

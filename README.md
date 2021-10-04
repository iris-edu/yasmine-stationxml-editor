# YASMINE

YASMINE (instrumentation metadata construction tool) is a python web application developed to generate metadata XML for a seismic stations.

## Requirements

1. Installed Python 3.6.5+
2. Related python packages will be installed automatically by pip

## Instructions to install (under super user rights)

1. Install a source distribution package ``pip install YASMINE-x.x.tar.gz``
2. Update database ``python yasmineapp.py syncdb upgrade heads``
3. If there is no internet connection unzip NRL (IRIS.zip) in to the application data folder "/opt/YASMINE/_media/" or "c:/YASMINE/_media/nrl/" depending on OS (Linux/Windows based).
4. Start application ``python yasmineapp.py runserver``

## Instructions to run using Docker

1. Install Docker <https://www.docker.com/products/docker-desktop>
2. Run `docker-compose up` to download, build and deploy docker container
3. Open browser and type `http://localhost:1841`

## Instructions to develop

1. To develop frontend, please go to `frontend` folder and see `README.md` file
2. To develop backend, please go to `backend` folder and see `README.md` file

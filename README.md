# YASMINE

YASMINE (Yet Another Station Metadata INformation Editor), is a python web application to create and edit station metadata information in FDSN stationXML format.
It is a common development of IRIS and Résif.
Development and addition of new features is shared and agreed between IRIS and Résif.


## Known issues
Even if we have performed a lot of tests, YASMINE is currently released in beta version and some bugs and limitations might still be found.

The new **AROL** (Atomic Response Objects Library) instrument response library, from Résif, is still in depoyment stage and only includes a limited set of instruments.
Users are encouraged to use the **NRL** library, also available.

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

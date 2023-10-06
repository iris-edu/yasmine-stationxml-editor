# Yasmine

Yasmine (Yet Another Station Metadata INformation Editor), is a Python web application to create and edit geophysical station metadata information in FDSN stationXML format.
This is a joint development of IRIS and Résif.
Development and addition of new features is shared and agreed upon between IRIS and Résif.


## Known issues
Even if we have performed a lot of tests, Yasmine is currently released in beta version and some bugs and limitations might still be found.

The new **AROL** (Atomic Response Objects Library) instrument response library, from Résif, is still in depoyment stage and only includes a limited set of instruments.
Users are encouraged to use the **NRL** library, also available.

## Instructions for users

### User Manual
Please read the included .docx manual for instructions on how to get started using Yasmine.

If there is no internet connection, unzip the bundled NRL (IRIS.zip) in the `data` folder at the root of this repository.

### Installation using Docker
1. Install [Docker Compose](https://docs.docker.com/compose/install/) or [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Run `docker-compose build` to compile and build the containers
3. Run `docker-compose up` to start
4. Visit <http://localhost:1841>
5. Run `docker-compose down` to stop

If you are running on an Apple M1 machine, uncomment the lines indicating the target platform in the `docker-compose.yml` file.

## Instructions for developers
1. To develop frontend, please go to `frontend` folder and see `README.md` file
2. To develop backend, please go to `backend` folder and see `README.md` file


## More information
* [Incorporated Research Institutions for Seismology (IRIS) Data Services](https://ds.iris.edu)
* [Réseau sismologique et géodésique français (Résif)](https://www.resif.fr/)
* [FDSN StationXML Manual](https://stationxml-doc.readthedocs.io/en/release-1.1.0/)
* [Nominal Response Library (NRL)](https://ds.iris.edu/ds/nrl/)

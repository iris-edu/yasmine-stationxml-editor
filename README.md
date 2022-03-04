# YASMINE

**YASMINE** (Yet Another Station Metadata INformation Editor) is a Python web application to create and edit geophysical station metadata information in FDSN stationXML format.
This is a joint development of IRIS and Résif.
Development and addition of new features is shared and agreed upon between IRIS and Résif.

## Known issues
YASMINE is currently released in beta version and some bugs and limitations might still be found.

The new **AROL** (Atomic Response Objects Library) instrument response library, from Résif, is still in depoyment stage and only includes a limited set of instruments.
Users are encouraged to use the **NRL** library, also available.

## Instructions for users

### User Manual
Please read the included .docx manual for instructions on how to get started using YASMINE.

### Installation using Docker
1. Install [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/5)
2. Run `docker-compose up` to build and run the docker containers
3. Visit <http://localhost:1841>
3. Run `docker-compose down` to stop

Note: Docker is the recommended method installation due to cross-platform incompatibilities with different Python package and environment managers. If an alternative installation method is desired, such as within a Python virtual environment, see 'Instructions for developers' below.

## Instructions for developers
1. To develop frontend, please go to `frontend` folder and see `README.md` file
2. To develop backend, please go to `backend` folder and see `README.md` file

## More information
* [Incorporated Research Institutions for Seismology (IRIS) Data Services](https://ds.iris.edu)
* [réseau sismologique et géodésique français (Résif)](https://www.resif.fr/)
* [FDSN StationXML Manual](https://stationxml-doc.readthedocs.io/en/release-1.1.0)
* [Nominal Response Library (NRL)](https://ds.iris.edu/ds/nrl/)

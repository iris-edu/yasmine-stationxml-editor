---
layout: page
title: Installation
permalink: /installation/
---

> **Latest version**: v4.1.0-beta

To install Yasmine, clone the application's repository:

```bash
 git clone https://github.iris.washington.edu/iris-edu/yasmine-stationxml-editor
```

### Running Yasmine

Yasmine may be started with Docker Compose or Python. Either way, the same data directory is used, so the choice is interchangable and a matter of preference.

> **Note:**
> The first installation may take up to ten minutes to complete as the instrument responses from the NRL are downloaded. Subsequently the application will function even while offline.

#### With Docker

Ensure you have [Docker Compose](https://docs.docker.com/compose/install/) installed:

```bash
 docker-compose --version
```

Run the following commands and visit <http://localhost:1841> when the application is available:

```bash
 cd yasmine-stationxml-editor
 docker-compose up
```

> **Important:**
> If you are running on an Apple M1 machine, uncomment the lines indicating the target platform in the `docker-compose.yml` file.

#### With Python

Ensure you have [Python](https://www.python.org/downloads/) 3.6.5 or greater installed:

```bash
 python --version
```

Run the following commands and visit <http://localhost:1841> when the 
application is available:

```bash
 python -m venv env
 source env/bin/activate
 pip install --upgrade pip setuptools
 pip install YASMINE-x.x.tar.gz
 sudo yasmineapp.py syncdb upgrade heads
 sudo yasmineapp.py runserver
```

<!-- ### Data Persistance -->
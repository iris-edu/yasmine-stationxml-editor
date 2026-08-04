---
layout: page
title: Installation
permalink: /installation/
---

> **Latest version**: v4.1.2-beta

To install Yasmine, clone the application's repository:

```bash
 git clone https://github.iris.washington.edu/iris-edu/yasmine-stationxml-editor
```

### Requirements

- **Python:** 3.13 recommended (supported: 3.9–3.13)
- **Key packages** (see [`backend/requirements.txt`](https://github.com/iris-edu/yasmine-stationxml-editor/blob/master/backend/requirements.txt) for the full list):
  - ObsPy >= 1.5.0
  - SQLAlchemy >= 2.0.51, < 2.1
  - Tornado >= 6.5.7
  - lxml >= 6.1.1
- **Transitive:** numpy and matplotlib are installed via ObsPy (not pinned directly)

Product releases are versioned as 4.x (see CHANGELOG). The setuptools package name is `YASMINE` with `version='1.0'` in setup.py — this is the internal package version, not the application release.

### Running Yasmine

Yasmine may be started with Docker Compose or Python. Either way, the same data directory is used, so the choice is interchangable and a matter of preference.

> **Note:**
> The first installation may take up to ten minutes to complete as the instrument responses from the NRL are downloaded. Subsequently the application will function even while offline.

#### With Docker

Ensure you have [Docker Compose](https://docs.docker.com/compose/install/) installed:

```bash
 docker compose version
```

Run the following commands and visit <http://localhost:1841> when the application is available:

```bash
 cd yasmine-stationxml-editor
 docker compose build
 docker compose up
```

Backend API: <http://localhost:8080/api/> (port mapping `8080:80` in `docker-compose.yml`).

> **Important:**
> If you are running on an Apple M1 machine, uncomment the lines indicating the target platform in the `docker-compose.yml` file.

#### With Python

Ensure you have [Python](https://www.python.org/downloads/) 3.13 installed (supported: 3.9–3.13):

```bash
 python --version
```

Run the following commands from the `backend` directory:

```bash
 cd yasmine-stationxml-editor/backend
 python -m venv env
 source env/bin/activate
 pip install --upgrade pip setuptools
 pip install -r requirements.txt
 yasmineapp.py syncdb upgrade heads
 yasmineapp.py runserver
```

Visit <http://localhost> when the backend is available (default port 80).

For the full GUI in development mode, build or watch the frontend separately — see [`frontend/README.md`](https://github.com/iris-edu/yasmine-stationxml-editor/blob/master/frontend/README.md) (`sencha app watch` serves the UI at <http://localhost:1841>).

| Scenario | URL | Notes |
|----------|-----|-------|
| Docker Compose (recommended) | <http://localhost:1841> | Frontend + backend |
| Backend only (`runserver`) | <http://localhost> | API and static assets after `sencha app build` |
| Frontend dev (`sencha app watch`) | <http://localhost:1841> | See frontend README |

<!-- ### Data Persistance -->

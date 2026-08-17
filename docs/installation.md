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
> **NRL Offline** is disabled by default. Enable it in **Settings** → *NRL Offline (download archive)* if you want Yasmine to download and maintain a local NRL copy under `data/_media/nrl/`.
>
> The **first download** of the full NRL ZIP (after enabling the option) may take ten minutes or longer depending on network speed. After a successful install, Yasmine works offline with the local library.
>
> **Update checks** use the IRIS NRL catalog endpoint with `updatedsince=<last successful install date>` (UTC calendar date in `data/_media/nrl/last_successful_download_date.txt`). If no configurations changed since that date, the full ZIP is not downloaded again. Checks run after startup and daily at 23:00 UTC. See `data/_logs/nrl.log` for sync status.

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

### NRL Offline library sync

Yasmine supports three response sources: **NRL Offline** (local archive), **NRLv2 Online** (on-demand API), and **AROL**. This section describes NRL Offline maintenance.

#### Enable and first install

1. Open **Settings** and enable **NRL Offline (download archive)** (`nrl__nrl_enabled`).
2. Restart the backend or wait for the startup sync job (~10 seconds after launch).
3. If no local library exists (`data/_media/nrl/content/NRL/`), Yasmine downloads the full NRL ZIP from:

   `https://service.iris.edu/irisws/nrl/1/combine?instconfig=full_NRL_v2_zip&format=resp.zip&nodata=404`

4. After a successful download and install, Yasmine writes the UTC install date to `data/_media/nrl/last_successful_download_date.txt` (`YYYY-MM-DD`).

#### Update checks (`updatedsince`)

After the first successful install, Yasmine no longer uses HTTP ETag for the full ZIP (the archive is generated dynamically and does not provide a reliable ETag). Instead it queries:

`https://service.iris.edu/irisws/nrl/1/catalog?element=*&format=text&level=configuration&updatedsince=<date>`

where `<date>` is the last successful install date. If the response contains only the CSV header, no update is available and the ZIP is not downloaded. If one or more configuration rows appear after the header, the full archive is downloaded and installed atomically.

Checks run once shortly after startup and daily at **23:00 UTC** (configurable via `NRL_CRON` in `backend/yasmine/app/settings.py`).

#### Logs and troubleshooting

Sync messages are written to `data/_logs/nrl.log`, for example:

- `Checking NRL updates since 2026-08-17`
- `No NRL updates found; archive download skipped`
- `NRL updates found; downloading full archive`
- `NRL archive updated successfully`
- `NRL catalog update check failed: ...`

If the catalog is unreachable or the download fails, the existing library under `data/_media/nrl/content/NRL/` is preserved; the install date file is not updated until a new archive is installed successfully.

#### Manual offline install

If you cannot reach IRIS during setup, unzip a bundled NRL archive so that `data/_media/nrl/content/NRL/` exists. Yasmine will initialize `last_successful_download_date.txt` on the next successful automatic install, or you may trigger a full download after enabling NRL Offline when connectivity is available.

<!-- ### Data Persistance -->

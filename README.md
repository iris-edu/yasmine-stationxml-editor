# Yasmine

Yasmine (Yet Another Station Metadata INformation Editor), is a Python web application to create and edit geophysical station metadata information in FDSN stationXML format.
This is a joint development of IRIS and Résif.
Development and addition of new features is shared and agreed upon between IRIS and Résif.
NRLv2 online support (2026): ASGSR, Alexey Emanov.

## Known issues

Even if we have performed a lot of tests, Yasmine is currently released in beta version and some bugs and limitations might still be found.

The new **AROL** (Atomic Response Objects Library) instrument response library, from Résif, is still in depoyment stage and only includes a limited set of instruments.
Users are encouraged to use the **NRL** library, also available.

## Instructions for users

### User Manual

Please read the included .docx manual for instructions on how to get started using Yasmine.

If there is no internet connection, enable **NRL Offline** in Settings (see below) only after placing a local NRL archive under `data/_media/nrl/content/NRL/`, or unzip bundled `IRIS.zip` into the repository `data/` folder as a fallback.

### NRL Offline

Yasmine can keep a **local copy** of the IRIS Nominal Response Library (full ZIP) for offline use.

1. Go to **Settings** and enable **NRL Offline (download archive)** (`nrl_enabled`)
2. On first start with this option enabled, Yasmine downloads the full NRL ZIP from the [IRIS NRL Web Service](https://service.earthscope.org/irisws/nrl/1/) (no catalog check on initial install)
3. After a successful install, Yasmine checks for updates via `GET /catalog?element=*&format=text&level=configuration&updatedsince=YYYY-MM-DD` — the UTC date of the last successful download
4. If the catalog response contains only the CSV header, the full ZIP is **not** re-downloaded; if one or more configuration rows appear after the header, a new full archive is downloaded and installed atomically
5. Checks run shortly after backend startup and daily at **23:00 UTC** (`NRL_CRON`)

**State and logs** (under `data/`):

| Path | Purpose |
| --- | --- |
| `_media/nrl/content/NRL/` | Installed offline library |
| `_media/nrl/last_successful_download_date.txt` | UTC date (`YYYY-MM-DD`) of last successful install; used as `updatedsince` |
| `_logs/nrl.log` | Sync messages (`Checking NRL updates since …`, skip/download/update/failure) |

Errors during catalog check or download do not remove the existing library. The date file is updated only after a successful install.

Requires internet for download and update checks. For on-demand responses without a local archive, use **NRLv2 Online** instead.

### NRLv2 Online

Yasmine supports **NRLv2 online** — using the [IRIS NRL Web Service](https://service.earthscope.org/irisws/nrl/1/) to fetch instrument responses on demand, without downloading the full NRL archive.

1. Go to **Settings** and enable **Online NRLv2**
2. Optionally set a custom **NRLv2 URL** (default: `https://service.earthscope.org/irisws/nrl/1/`)
3. Use the **Test** button to verify connectivity
4. When selecting a response (e.g. "Select a new Response"), choose **NRLv2 online** and follow the wizard: Element type → Manufacturer → Model → Configuration

Requires internet access. Disable in Settings when working offline.

As of 20 August 2026 the NRL service is at `service.earthscope.org` (formerly `service.iris.edu`; redirects start 24 August 2026). Run `yasmineapp.py syncdb upgrade heads` so existing databases that still store the old default URL are migrated. Custom URLs (for example NRLaggregator) are left unchanged.

### Installation using Docker

1. Install [Docker Compose](https://docs.docker.com/compose/install/) or [Docker Desktop](https://www.docker.com/products/docker-desktop)
2. Run `docker compose build` to compile and build the containers
3. Run `docker compose up` to start
4. Visit <http://localhost:1841>
5. Backend API: <http://localhost:8080/api/> (when using docker compose)
6. Run `docker compose down` to stop

For Python-based installation, see [`backend/README.md`](backend/README.md).

If you are running on an Apple M1 machine, uncomment the lines indicating the target platform in the `docker-compose.yml` file.

## Instructions for developers

1. To develop frontend, please go to `frontend` folder and see `README.md` file
2. To develop backend, please go to `backend` folder and see `README.md` file

## More information

* [Incorporated Research Institutions for Seismology (IRIS) Data Services](https://ds.iris.edu)
* [Réseau sismologique et géodésique français (Résif)](https://www.resif.fr/)
* [FDSN StationXML Manual](https://stationxml-doc.readthedocs.io/en/release-1.1.0/)
* [Nominal Response Library (NRL)](https://ds.iris.edu/ds/nrl/)

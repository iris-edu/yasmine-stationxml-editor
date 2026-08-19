# YASMINE Backend

If GUI is required to be used, please see `../frontend/README.md` before using backend

## Requirements

- **Python:** 3.13 recommended (supported: 3.9–3.13)
- **Key packages** (see `requirements.txt` for full list):
  - ObsPy >= 1.5.0
  - SQLAlchemy >= 2.0.51, < 2.1
  - Tornado >= 6.5.7
  - lxml >= 6.1.1
- **Transitive:** numpy and matplotlib are installed via ObsPy (not pinned directly)

Product releases are versioned as 4.x (see CHANGELOG). The setuptools package name is `YASMINE` with `version='1.0'` in setup.py — this is the internal package version, not the application release.

## Using python virtual environment

1. Install Python 3.13 (supported: 3.9–3.13)
2. Run `python -m venv env`
3. Run `source env/bin/activate`
4. Run `pip install --upgrade pip setuptools`
5. Run `pip install -r requirements.txt`
6. Run `yasmineapp.py syncdb upgrade heads`
7. Run `yasmineapp.py runserver`

## Using Docker

**Standalone backend image** (not Docker Compose):

1. Install Docker <https://www.docker.com/products/docker-desktop>
2. Build Docker image: `docker build -t yasmine/backend .`
3. Run Docker image: `docker run --rm -p 80:80 yasmine/backend`
4. Go to GUI url: <http://localhost>
5. Go to REST API endpoint: <http://localhost/api/>

For the full development stack (frontend + backend), use `docker compose` from the repository root — see the root README. The UI is at <http://localhost:1841>; the backend API is at <http://localhost:8080/api/>.

## Tips

1. To generate a DB migration script: `python yasmineapp.py syncdb revision --autogenerate`
2. To apply DB migrations: `python yasmineapp.py syncdb upgrade heads`
3. To run all unittests `python yasmineapp.py test`

## NRL Offline sync (backend)

When **NRL Offline** is enabled in Settings (`nrl_enabled`), the scheduler runs `sync_nrl` shortly after startup and daily at 23:00 UTC (`NRL_CRON` in `yasmine/app/settings.py`).

- **Initial install** (no `data/_media/nrl/content/NRL/`): downloads the full NRL ZIP without a catalog pre-check.
- **Subsequent checks**: `GET https://service.earthscope.org/irisws/nrl/1/catalog?element=*&format=text&level=configuration&updatedsince=YYYY-MM-DD` where the date comes from `data/_media/nrl/last_successful_download_date.txt`.
- **No updates**: catalog response is CSV header only → skip download.
- **Updates available**: one or more data rows after the header → download, validate, and atomically replace the local library.
- **Logs**: `data/_logs/nrl.log`

The legacy ETag check on the full-ZIP URL is no longer used for NRL Offline (ETag remains for AROL sync).

Unit tests: `python -m unittest yasmine.app.tests.unit.nrl_catalog_sync_test`

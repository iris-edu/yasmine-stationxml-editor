# YASMINE Backend

If GUI is required to be used, please see `../frontend/README.md` before using backend

## Requirements

- **Python:** 3.13 recommended (supported: 3.9–3.13)
- **Key packages** (see `requirements.txt` for full list):
  - ObsPy >= 1.5.1
  - SQLAlchemy >= 2.0.54, < 2.1
  - Tornado >= 6.5.10
  - lxml >= 6.1.3
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
2. Build Docker image from the repository root: `docker build -f backend/Dockerfile -t yasmine/backend .`
3. Run Docker image: `docker run --rm -p 80:80 yasmine/backend`
4. Go to GUI url: <http://localhost>
5. Go to REST API endpoint: <http://localhost/api/>

For the full development stack (frontend + backend), use `docker compose` from the repository root — see the root README. The UI is at <http://localhost:1841>; the backend API is at <http://localhost:8080/api/>.

## Tips

1. To generate a DB migration script: `python yasmineapp.py syncdb revision --autogenerate`
2. To apply DB migrations: `python yasmineapp.py syncdb upgrade heads`
3. To run unit, HTTP, and integration tests: `python yasmineapp.py test`
4. Selenium GUI tests need a running app and a browser: `python yasmineapp.py test --gui` sets `YASMINE_TEST_GUI=1` before tests load (optional `YASMINE_TEST_HOST` / `YASMINE_TEST_PORT`, e.g. Compose UI at `127.0.0.1:1841`)
5. Tests that download NRL or AROL: `python yasmineapp.py test --network` (sets `YASMINE_TEST_NETWORK=1` the same way)

## NRL Offline sync (backend)

When **NRL Offline (download archive)** is enabled in Settings (stored as `nrl_enabled`), the scheduler runs `sync_nrl` about 10 seconds after startup and daily at 23:00 UTC (`NRL_CRON` in `yasmine/app/settings.py`).

- **Initial install** (no `data/_media/nrl/content/NRL/`): downloads the full NRL ZIP without a catalog pre-check.
- **Subsequent checks**: `GET https://service.earthscope.org/irisws/nrl/1/catalog?element=*&format=text&level=configuration&updatedsince=YYYY-MM-DD` where the date comes from `data/_media/nrl/last_successful_download_date.txt`.
- **No updates**: catalog response is CSV header only → skip download.
- **Updates available**: one or more data rows after the header → download, validate, and atomically replace the local library.
- **Logs**: `data/_logs/nrl.log`

The legacy ETag check on the full-ZIP URL is no longer used for NRL Offline (ETag remains for AROL sync).

Unit tests: `python -m unittest yasmine.app.tests.unit.nrl_catalog_sync_test`

## StationXML 1.2 help and schema

The unmodified FDSN StationXML 1.2 XSD is vendored at
`yasmine/resources/schemas/stationxml/1.2/fdsn-station-1.2.xsd`. Generated
help catalogs live beside it. The schema help API is
`/api/stationxml/help/1.2/` and is separate from GATITO `/api/help/` and
`/api/helper/`.

Regenerate catalogs after an XSD update:

```bash
python tools/generate_stationxml_help.py
```

Export sets `schemaVersion` to `1.2`, validates the file against that XSD,
and returns HTTP 400 with reason `StationXML 1.2 export blocked` when schema
errors are present. `GET /api/xml/validate/<id>` also returns non-blocking
Yasmine recommendations. `POST /api/channel/response/validate/` checks a
response tree and includes operational notes that do not make the tree
invalid. See `docs/stationxml-context-help.md` and
`docs/stationxml-1.2-coverage.md`.

**NRL Online** is the Settings fieldset for the NRL Web Service. The checkbox
is **NRL Online** (`nrlv2_online_enabled`) and the URL field is **NRL URL**
(`nrlv2_base_url`, default `https://service.earthscope.org/irisws/nrl/1/`).

The response selector loads `sensor` and `datalogger` for **Datalogger + sensor**,
and `integrated` or `soh` for a single instrument
(`GET /api/nrl/<element>/` offline, `GET /api/nrlv2/<element>/` online).
An offline directory that is missing or empty returns the leaf text
`This response type is not in the downloaded NRL`.
**Integrated** fills both channel Sensor and DataLogger. **SOH** fills DataLogger.

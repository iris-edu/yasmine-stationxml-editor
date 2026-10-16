# Yasmine

Yasmine (Yet Another Station Metadata INformation Editor) is a Python web application to create and edit geophysical station metadata in [FDSN StationXML 1.2](https://docs.fdsn.org/projects/stationxml/en/v1.2/).
Export writes `schemaVersion="1.2"` and validates the file against the vendored schema `backend/yasmine/resources/schemas/stationxml/1.2/fdsn-station-1.2.xsd`.
This is a joint development of IRIS and Résif.
Development and addition of new features is shared and agreed upon between IRIS and Résif.
Version 4.4.0 of the software was developed by ASGSR, the Altay-Sayan Branch of the Geophysical Survey of the Russian Academy of Science.
NRL Online support (2026): ASGSR, Alexey Emanov.

Current version: 4.4.0-beta.

## Known issues

Even if we have performed a lot of tests, Yasmine is currently released in beta version and some bugs and limitations might still be found.

**Security / deployment.** The Tornado HTTP API has no application login. Treat a running instance as trusted-LAN (or reverse-proxy auth) only — do not expose the API port on the public internet.

**Validation.** Export is refused only for StationXML 1.2 XSD errors. **File → Strict Validate XML** warnings never block download; XSD-valid does not mean archive-ready.

**AROL limits.** The **AROL** (Atomic Response Objects Library) from Résif is still being deployed and includes a limited set of instruments. It has no Integrated/SOH response-type step (unlike NRL Offline/Online). Channel codes are suggested via SEED `seed_channel_prefix` when responses expose rate/units; empty suggests mean the YAML lacked usable rate/units. The AROL response builder still contains temporary PZ `units` → transfer-function mapping and DECIMATION input-unit overrides until the library YAML is fixed upstream. Prefer **NRL Offline** or **NRL Online** for Nominal Response Library workflows.

**Sidecars.** Foreign-namespace StationXML extensions are stored as opaque sidecars (read-only **Extensions** on the Hierarchy toolbar). Deleting a node permanently removes its sidecar and those of its descendants — the confirm dialog reports the count.

**DataAvailability.** Span-only blocks may receive a temporary Extent on import so ObsPy can read the file; export omits that Extent when spans remain. See the post-import migration notes dialog.

**Polynomial responses.** Recalculate Sensitivity is disabled for InstrumentPolynomial channels (no overall sensitivity). Polynomial plots default to a ±20 V output sweep unless approximation bounds are in volts.

**Selenium tests.** `python yasmineapp.py test --gui` enables the GUI suite (also `YASMINE_TEST_GUI=1`). Point the browser at the UI with `YASMINE_TEST_HOST` / `YASMINE_TEST_PORT` (Compose UI is usually `127.0.0.1:1841`).

## Instructions for users

### User Manual

Start with [`docs/user-guide.md`](docs/user-guide.md). Field help in the editor is the English text of the StationXML 1.2 XSD; see [`docs/stationxml-context-help.md`](docs/stationxml-context-help.md). The field checklist is [`docs/stationxml-1.2-coverage.md`](docs/stationxml-1.2-coverage.md).

For offline responses, place a local NRL tree at `data/_media/nrl/content/NRL/` and then enable **NRL Offline (download archive)** in Settings. The repository does not ship an NRL archive.

### NRL Offline

Yasmine can keep a **local copy** of the IRIS Nominal Response Library (full ZIP) for offline use.

1. Go to **Settings** and enable **NRL Offline (download archive)** (stored as `nrl_enabled`)
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

In the channel wizard and the channel response editor, **NRL Offline** then asks for a response type: **Datalogger + sensor**, **Integrated**, or **SOH**. Integrated and SOH are read from the `integrated` and `soh` directories of the local archive. A missing directory shows `This response type is not in the downloaded NRL`. **Integrated** fills both channel Sensor and DataLogger. **SOH** fills DataLogger.

Requires internet for download and update checks. For on-demand responses without a local archive, use **NRL Online**.

### NRL Online

Yasmine can use the [EarthScope NRL Web Service](https://service.earthscope.org/irisws/nrl/1/) (NRLv2) to fetch instrument responses on demand, without downloading the full NRL archive.

1. Go to **Settings**, open **NRL Online**, and enable **NRL Online** (stored as `nrlv2_online_enabled`)
2. Optionally set **NRL URL** (stored as `nrlv2_base_url`; default `https://service.earthscope.org/irisws/nrl/1/`)
3. Use **Test** to verify connectivity
4. In the channel wizard, choose **NRL Online**, then **Datalogger + sensor**, **Integrated**, or **SOH**. The library choice stays disabled until the setting is on. **Datalogger + sensor** uses separate Datalogger and Sensor tabs and walks manufacturer, model, and configuration on each. **Integrated** and **SOH** use one tab for that element and the same walk. The channel response editor offers the same three choices. **Integrated** fills both channel Sensor and DataLogger. **SOH** fills DataLogger

Requires internet access. Leave **NRL Online** off when working offline.

### Station map

In the builder, **Map** opens the stations of the current inventory, network, station, or channel. **Select Epoch** limits the markers to that date. Stations are shown first; **Channels** loads channel markers. A channel is omitted when its station is not active at the selected epoch. Names use `NET.STA` and `NET.STA.LOC.CHA`. Basemap tiles are fetched by the Yasmine server from OpenStreetMap or OpenTopoMap. **Download** saves the current view as a PNG. Details are in [`docs/user-guide.md`](docs/user-guide.md).

As of 20 August 2026 the NRL service is at `service.earthscope.org` (the former `service.iris.edu` host redirects from 24 August 2026). Run `yasmineapp.py syncdb upgrade heads` so existing databases that still store the old default URL are migrated. A custom URL, for example an NRLaggregator, is left unchanged.

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
* [FDSN StationXML 1.2 Manual](https://docs.fdsn.org/projects/stationxml/en/v1.2/)
* [Nominal Response Library (NRL)](https://ds.iris.edu/ds/nrl/)

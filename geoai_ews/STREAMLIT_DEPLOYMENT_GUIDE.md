# Streamlit Deployment Guide
### North Rift GeoAI + Agentic EWS

This guide explains how to upload/wire the `geoai/`, `ews/`, `db/`, and
`messaging/` modules into a working Streamlit application, run it locally,
and deploy it — either on Streamlit Community Cloud or on your own server.

---

## 1. What's already built for you

Inside the zip you received, there's now a `streamlit_app/` folder:

```
streamlit_app/
  streamlit_app.py                Home page / entry point
  secrets_bridge.py                Bridges st.secrets -> the env vars config/settings.py already reads
  pages/
    1_Credentials_Status.py        Shows which credentials are loaded (never the values)
    2_Upload_Boundaries.py         Upload county/ward GeoJSON
    3_DEM_and_Terrain.py           Upload GLO-30 DEM, compute slope/hillshade
    4_Borehole_and_Recharge_Index.py  Upload/fetch borehole points, compute risk grid
    5_Earth_Index_Embeddings.py    Upload embedding tiles, score anomalies
    6_Advisory_Cycle.py            Interactive walkthrough of the 10-step workflow
.streamlit/
  secrets.toml.example             Template for your credentials (Streamlit's format)
```

**Nothing in `geoai/` or `ews/` needed to change.** Streamlit is just a thin
interactive layer that imports and calls the same functions your pipeline
and orchestrator already use — this keeps one source of truth for the logic.

---

## 2. Two ways to "upload the modules" into Streamlit

### Option A — Run locally, upload data through the browser (fastest to test)

1. Install dependencies:
   ```bash
   cd ews  # your repo root (this project lives at geoai_ews/ inside it)
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy the secrets template and fill in what you have so far:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
3. Launch the app:
   ```bash
   streamlit run streamlit_app/streamlit_app.py
   ```
4. Your browser opens automatically (usually `http://localhost:8501`).
   Use the sidebar pages to **upload files directly through the UI** —
   boundary GeoJSONs, a DEM GeoTIFF, borehole CSV/GeoJSON, Earth Index
   embedding `.parquet` tiles. The code modules themselves are already
   "uploaded" because they live in the project folder — you're uploading
   *data*, not code, through this interface.

### Option B — Deploy the whole codebase to Streamlit Community Cloud

This is what people usually mean by "uploading modules to Streamlit" — getting
your whole `geoai`/`ews` codebase onto Streamlit's hosting so others can use
the app without you running anything locally.

1. **Push the project to GitHub** (Streamlit Cloud deploys from a GitHub repo,
   it does not accept a raw zip upload):
   ```bash
   cd ews  # your repo root (this project lives at geoai_ews/ inside it)
   git init
   git add .
   git commit -m "Initial North Rift GeoAI + Agentic EWS app"
   git remote add origin https://github.com/<your-username>/ews.git
   git push -u origin main
   ```
   *(You already have a working local→push pattern for this from earlier —
   local packaging → manual `git push`, since GitHub MCP isn't available here.)*

2. **Go to** [share.streamlit.io](https://share.streamlit.io) and sign in with
   GitHub.

3. **Click "New app"**, then:
   - Repository: `<your-username>/ews`
   - Branch: `main`
   - Main file path: `geoai_ews/streamlit_app/streamlit_app.py`

4. **Add your secrets** — in the app's "Settings → Secrets" panel, paste the
   contents of your filled-in `secrets.toml` (never commit the real file to
   GitHub; `.streamlit/secrets.toml` should stay in `.gitignore`).

5. Click **Deploy**. Streamlit Cloud installs `requirements.txt` and runs
   `streamlit_app/streamlit_app.py` automatically. Redeploys happen automatically on
   every `git push` to the branch.

---

## 3. Wiring credentials into Streamlit specifically

Your existing `config/settings.py` reads plain environment variables (via
`.env` + `python-dotenv`). Streamlit doesn't use `.env` files — it uses
`st.secrets`, backed by a `secrets.toml` file (local) or the Secrets panel
(cloud).

`streamlit_app/secrets_bridge.py` solves this: it copies every value out of
`st.secrets` into `os.environ` **before** any `geoai`/`ews`/`db`/`messaging`
module is imported, so those modules keep working completely unaware they're
running inside Streamlit.

```python
# Already wired into streamlit_app/streamlit_app.py — for reference:
from streamlit_app.secrets_bridge import load_secrets_into_env
load_secrets_into_env()          # must run before importing config/geoai/ews
```

Fill in `.streamlit/secrets.toml` (local) or the cloud Secrets panel using
the same values documented in `CREDENTIALS_AND_ACCESS_REQUIRED.pdf` — the
section headers (`[copernicus]`, `[earth_index]`, `[wra_wris]`, etc.) map
1:1 to that document.

### Special case: Google Earth Engine service-account JSON

`GEE_SERVICE_ACCOUNT_KEY_PATH` expects a file path locally. On Streamlit
Cloud there's no persistent file to point at, so instead:
1. Paste the **entire JSON key content** (not a path) into a secret, e.g.
   `gee_key_json = '''{...}'''` under `[gee]`.
2. At app startup, write it to a temp file and set the env var to that path:
   ```python
   import json, tempfile
   key_json = st.secrets["gee"]["gee_key_json"]
   with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
       f.write(key_json)
       os.environ["GEE_SERVICE_ACCOUNT_KEY_PATH"] = f.name
   ```

---

## 4. Persisting uploaded files (important limitation)

Streamlit Community Cloud's filesystem is **ephemeral** — anything saved to
`data/boundaries/`, `data/terrain/`, etc. disappears on redeploy or when the
app goes to sleep. For anything beyond quick testing:

- **Boundaries / small reference files**: commit verified GeoJSON directly
  into the repo under `data/boundaries/` — these rarely change.
- **DEM tiles, embeddings, risk grids**: write to your PostGIS database
  (`db/models.py` already has `RiskGridCell`) or to an external object store
  (S3-compatible bucket) instead of local disk.
- **Farmer/advisory records**: already designed to live in PostGIS/
  TimescaleDB via `DATABASE_URL` — this is unaffected by Streamlit's
  ephemeral filesystem since the database is external.

---

## 5. Turning this into the full agentic app (beyond the demo pages)

The six pages shipped are deliberately scoped as an **interactive console**
for each module — good for validating logic, uploading test data, and
demoing to stakeholders. To power a real production advisory loop from
Streamlit:

- Add a page that calls `scripts/run_scheduled_cycle.run_all_plots_once()`
  on a button click, backed by a real `DATABASE_URL`.
- Add a farmer-registration form page wired to
  `ews/onboarding_agent.OnboardingAgent`.
- For true "always-on" scheduling (weekly cycles), Streamlit itself isn't a
  scheduler — keep `scripts/run_scheduled_cycle.py --daemon` running as a
  separate background process (e.g. a small VM, or a scheduled GitHub
  Action / cron job) and use Streamlit purely as the human-facing dashboard
  that reads from the same database.

---

## 6. Troubleshooting: "ModuleNotFoundError: geopandas / rasterio" on Streamlit Cloud

If your deployed app's logs show only ~40 packages installed (Streamlit's own
dependencies) and every page importing `geoai/` crashes with
`ModuleNotFoundError`, Streamlit Cloud did not find/install your project's
`requirements.txt`. This was diagnosed from an actual deployment log — see
`Streamlit_Deployment_Log_Analysis_and_Recommendations.pdf` for the full
analysis. The fix, already applied in this codebase:

1. **`packages.txt`** (repo root) — installs the system-level GDAL/PROJ
   libraries that geopandas/rasterio/fiona need beyond their Python wheels:
   ```
   gdal-bin
   libgdal-dev
   libspatialindex-dev
   libproj-dev
   proj-bin
   ```
2. **`runtime.txt`** (repo root) — pins a Python version with broad
   prebuilt-wheel support for geospatial packages:
   ```
   python-3.12
   ```
3. **`requirements-streamlit-cloud.txt`** — a trimmed dependency list with
   only what the demo pages need (geopandas, rasterio, shapely, pyproj,
   fiona, numpy, pandas, pyarrow, scikit-learn, streamlit, requests,
   python-dotenv), skipping the backend-only packages
   (SQLAlchemy/GeoAlchemy2/psycopg2-binary/twilio/APScheduler) that only
   `scripts/run_scheduled_cycle.py` needs. If you use this file, set it
   explicitly under **App settings → Advanced settings → Python dependencies
   file** in Streamlit Cloud.
4. **`richdem` removed** from `requirements.txt` — it was never actually
   imported (terrain derivatives use plain numpy gradients) and needlessly
   required a C++ compiler/cmake step.

**Critical placement check:** all three files above (`packages.txt`,
`runtime.txt`, `requirements.txt` / `requirements-streamlit-cloud.txt`) must
sit at the **root of your GitHub repository** — not inside this `geoai_ews/`
project folder — since your main file lives at
`geoai_ews/streamlit_app/streamlit_app.py`. **This was diagnosed as the
actual root cause from a live deployment log**, and this zip's own top level
is now pre-structured to match: when you unzip it, `packages.txt`,
`runtime.txt`, and the requirements files sit one level above `geoai_ews/` —
see `README_FIRST_REPO_PLACEMENT.md` at the very top of the zip for exact
copy/merge instructions into your existing `ews` repo. Verify after pushing
with:
```bash
git ls-files | grep -E "requirements|packages.txt|runtime.txt"
```
Confirm none of these paths are prefixed with `geoai_ews/`.

After pushing these changes, reboot the app ("Manage app → Reboot") and
confirm the build log now lists geopandas, rasterio, shapely, etc. among the
installed packages.

---

## 7. Quick checklist

- [ ] `pip install -r requirements.txt` (now includes `streamlit`)
- [ ] `cp .streamlit/secrets.toml.example .streamlit/secrets.toml` and fill in
      what credentials you already have
- [ ] `streamlit run streamlit_app/streamlit_app.py` — confirm the Credentials Status
      page reflects what you filled in
- [ ] Push to GitHub, deploy on Streamlit Community Cloud, paste secrets into
      the cloud Secrets panel
- [ ] Decide where uploaded/derived data will actually persist (repo, DB, or
      bucket) before relying on this beyond local testing
- [ ] Confirm `packages.txt` and `runtime.txt` are committed at your GitHub
      repo's true root (`git ls-files | grep -E "packages.txt|runtime.txt"`)
- [ ] After pushing, use **Reboot app** from the "⋮" menu in Streamlit Cloud
      — do not rely on the automatic hot-update from a push alone; it was
      observed to skip re-resolving dependencies entirely
- [ ] After any Streamlit Cloud deploy, check the build log for geopandas/
      rasterio/shapely/fiona actually appearing in the "Installed N packages"
      list — if they're missing, revisit section 6 above

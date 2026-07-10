# READ THIS FIRST — Repo Placement Fix

Your Streamlit Cloud deployment logs showed `ModuleNotFoundError: geopandas`
and `ModuleNotFoundError: rasterio` on every page that needed them, even
after adding `packages.txt`/`runtime.txt`/an updated `requirements.txt`.
The build logs proved those files were never actually being read by
Streamlit Cloud — most likely because they'd been committed *inside* the
`geoai_ews/` project folder instead of at the true root of your `ews`
GitHub repository.

**This zip is now structured exactly as your `ews` repo root should look:**

```
(zip root = your "ews" repo root)
├── packages.txt                  <- MUST be at repo root (Streamlit Cloud requirement)
├── runtime.txt                   <- MUST be at repo root
├── requirements.txt              <- repo root (or set an explicit path in Streamlit's
├── requirements-streamlit-cloud.txt   Advanced settings if you keep it elsewhere)
├── .gitignore
└── geoai_ews/                    <- your project folder (unchanged internally)
    ├── streamlit_app/
    │   └── streamlit_app.py      <- your app's main file path stays
    │                                geoai_ews/streamlit_app/streamlit_app.py
    ├── geoai/
    ├── ews/
    ├── db/
    ├── messaging/
    ├── config/
    ├── tests/
    ├── scripts/
    ├── data/
    ├── pipeline.py
    ├── README.md
    ├── STREAMLIT_DEPLOYMENT_GUIDE.md
    ├── CREDENTIALS_AND_ACCESS_REQUIRED.pdf
    ├── .env.example
    └── .streamlit/secrets.toml.example
```

## How to apply this to your existing GitHub repo

1. Unzip this archive.
2. Copy `packages.txt`, `runtime.txt`, `requirements.txt`,
   `requirements-streamlit-cloud.txt`, and `.gitignore` into the **root** of
   your local `ews` repo clone (same level as your existing `geoai_ews/`
   folder — do NOT put them inside it).
3. Replace your existing `geoai_ews/` folder with the one in this zip
   (it contains the same fixes already applied: `richdem` removed from
   requirements, the `use_container_width` fix in
   `streamlit_app/pages/1_Credentials_Status.py`, etc.) — or diff/merge if
   you have local changes you want to keep.
4. Commit and push:
   ```bash
   git add packages.txt runtime.txt requirements.txt requirements-streamlit-cloud.txt .gitignore geoai_ews
   git commit -m "Move dependency files to repo root; fix Streamlit Cloud build"
   git push
   ```
5. **Important:** in the Streamlit Cloud dashboard, open the app's "⋮" menu
   and click **Reboot app** — don't just wait for the automatic hot-update
   from the push. A push-triggered update alone was observed to skip
   re-resolving dependencies; a forced reboot rebuilds the environment from
   scratch and will pick up `packages.txt`/`runtime.txt` correctly.
6. Watch the new build log for an `Installing Streamlit` section listing
   **more than 42 packages** — confirm `geopandas`, `rasterio`, `shapely`,
   and `fiona` appear by name.

If, after this, the same 42-package/ModuleNotFoundError pattern still
appears, the next step is to delete the Streamlit Cloud app entirely and
redeploy fresh, which guarantees no stale cached container is reused.

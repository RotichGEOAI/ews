"""Upload Earth Index embedding tiles (GeoParquet) and score anomalies."""
import sys
import tempfile
from pathlib import Path

import numpy as np
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from geoai.earth_index_client import load_embeddings
from geoai.anomaly_scoring import compute_anomaly_scores

st.title("🛰️ Earth Index Embeddings — Anomaly Scoring")
st.caption(
    "Download GeoParquet tiles from Source Cooperative "
    "(earthgenome/earthindexembeddings) ahead of time, or via "
    "geoai/earth_index_client.py if EARTH_INDEX_SOURCE_COOP_TOKEN is set, "
    "then upload the .parquet file here."
)

uploaded = st.file_uploader("Upload embeddings GeoParquet tile", type=["parquet"])

if uploaded is not None:
    with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
        tmp.write(uploaded.read())
        tmp_path = Path(tmp.name)

    tiles = load_embeddings(tmp_path)
    st.success(f"Loaded {len(tiles)} embedding tile(s).")
    st.map(tiles)

    st.subheader("Reference signature")
    n_refs = st.number_input("Number of reference tile IDs to flag as the stress pattern", 1, 10, 1)
    ref_ids = []
    for i in range(int(n_refs)):
        ref_id = st.selectbox(f"Reference tile #{i+1}", tiles["id"].tolist(), key=f"ref_{i}")
        ref_ids.append(ref_id)

    if st.button("Score anomalies against selected reference(s)"):
        ref_embeddings = np.vstack(
            tiles[tiles["id"].isin(ref_ids)]["embedding"].to_numpy()
        )
        scored = compute_anomaly_scores(tiles, ref_embeddings)
        st.session_state["embedding_scores"] = scored
        st.dataframe(scored[["id", "similarity_score", "anomaly_score"]].sort_values(
            "anomaly_score", ascending=False
        ).head(30))
        st.bar_chart(scored.set_index("id")["anomaly_score"])

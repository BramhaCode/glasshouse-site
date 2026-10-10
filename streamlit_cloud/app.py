"""
GlassHouse website launcher for Streamlit Community Cloud. This repo holds no app code or data: on first start it
downloads the bundle (code + slim database, built by deploy/build_site_bundle.py) from a PRIVATE Hugging Face
dataset, unpacks it and runs SubscriberApp.py. Secrets (set in the app's Settings → Secrets): HF_TOKEN (read
token), BUNDLE_REPO, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, APP_URL.
To load a new bundle: upload it, then Reboot the app from share.streamlit.io.
"""
import os
import runpy
import shutil
import sys
import tarfile
from pathlib import Path

import streamlit as st

os.environ["GLASSHOUSE_DEPLOYED"] = "1"        # a hosted copy: never "running locally", so never auto-admin
REQUIRED = ("HF_TOKEN", "BUNDLE_REPO", "GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET", "GOOGLE_REDIRECT_URI", "APP_URL")
try:                                           # root-level secrets → environment (the app reads os.environ)
    for key, value in st.secrets.items():
        if isinstance(value, (str, int, float, bool)):
            os.environ.setdefault(key, str(value))
except Exception:
    pass
missing = [k for k in REQUIRED if not os.environ.get(k)]
if missing:                                    # names only — never values
    st.error("The site isn't configured yet. Missing secrets: " + ", ".join(missing) + ". Add them under Manage "
             "app → Settings → Secrets (top level, no [section] header), save, then Reboot the app.")
    st.stop()

SITE = Path(os.environ.get("GLASSHOUSE_SITE_DIR", "/tmp/glasshouse_site"))


@st.cache_resource(show_spinner=False)
def unpack() -> str:
    """Download and unpack the private bundle once per server process."""
    from huggingface_hub import hf_hub_download
    path = hf_hub_download(repo_id=os.environ["BUNDLE_REPO"], repo_type="dataset",
                           filename="glasshouse_site.tar.gz", token=os.environ["HF_TOKEN"])
    fresh = SITE.with_name(SITE.name + "_new")
    shutil.rmtree(fresh, ignore_errors=True)
    with tarfile.open(path) as tar:
        tar.extractall(fresh, filter="data")
    shutil.rmtree(SITE, ignore_errors=True)
    fresh.rename(SITE)
    return str(SITE)


site = unpack()
os.environ["MOMENTUM_DATA_DIR"] = os.path.join(site, "data")
if site not in sys.path:
    sys.path.insert(0, site)
os.chdir(site)
runpy.run_path(os.path.join(site, "SubscriberApp.py"), run_name="__main__")

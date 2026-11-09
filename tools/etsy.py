"""Etsy API v3 helper for Pale North Studio (own shop only). No secrets in this file.

Secrets live in the PRIVATE repo ludvigwallertoft/palenorth-secrets, cloned to $SECRETS (default /tmp/pns):
  etsy.json    {"keystring": "...", "shared_secret": "..."}   (written by the owner)
  tokens.json  {"access_token","refresh_token","expires_at","user_id","shop_id"} (written by this tool)
  pkce.json    pending OAuth verifier/state (written by this tool)
Never print secrets. After any command that changes tokens.json, commit + push the secrets repo.

Commands
  python3 tools/etsy.py auth-url                 -> prints the one-time consent URL for the owner
  python3 tools/etsy.py exchange --code CODE     -> stores tokens
  python3 tools/etsy.py ping                     -> refreshes token if needed, prints shop name/id
  python3 tools/etsy.py taxonomy --q "digital prints"
  python3 tools/etsy.py publish --package listing.json [--draft]
     listing.json: {"title","description","price_sek","tags":[13],"taxonomy_id"(opt),"images":[paths max 10],
                    "files":[paths max 5, each <=20MB],"materials":[],"slug"}
     -> creates the listing as a digital download, uploads images and files, activates it (unless --draft),
        prints {"listing_id","url","state"}
"""
import argparse, base64, hashlib, json, os, secrets as pysecrets, subprocess, sys, time

try:
    import requests
except ImportError:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "requests", "--break-system-packages"], check=True)
    import requests

SECRETS = os.environ.get("SECRETS", "/tmp/pns")
API = "https://openapi.etsy.com/v3/application"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
REDIRECT = "https://palenorthstudios.etsy.com/"
SCOPES = "listings_r listings_w shops_r"


def jload(name, default=None):
    p = os.path.join(SECRETS, name)
    return json.load(open(p)) if os.path.exists(p) else default


def jsave(name, data):
    json.dump(data, open(os.path.join(SECRETS, name), "w"), indent=1)


def app():
    a = jload("etsy.json")
    if not a:
        sys.exit("etsy.json missing in secrets repo")
    return a


def api_key_headers():
    a = app()
    # Etsy accepts "keystring:shared_secret"; older apps accept the keystring alone
    return [{"x-api-key": f"{a['keystring']}:{a['shared_secret']}"}, {"x-api-key": a["keystring"]}]


def token_request(data):
    data = dict(data, client_id=app()["keystring"])
    r = requests.post(TOKEN_URL, data=data, timeout=30)
    if r.status_code != 200:
        sys.exit(f"token error {r.status_code}: {r.text[:300]}")
    t = r.json()
    tok = jload("tokens.json", {})
    tok.update(access_token=t["access_token"], refresh_token=t["refresh_token"],
               expires_at=time.time() + int(t.get("expires_in", 3600)) - 120,
               user_id=t["access_token"].split(".")[0])
    jsave("tokens.json", tok)
    return tok


def token():
    tok = jload("tokens.json")
    if not tok:
        sys.exit("not authorised yet: run auth-url and exchange")
    if time.time() > tok.get("expires_at", 0):
        tok = token_request({"grant_type": "refresh_token", "refresh_token": tok["refresh_token"]})
    return tok


def call(method, path, **kw):
    tok = token()
    last = None
    for h in api_key_headers():
        headers = dict(h, Authorization=f"Bearer {tok['access_token']}")
        r = requests.request(method, API + path, headers=headers, timeout=120, **kw)
        if r.status_code not in (401, 403) or "api key" not in r.text.lower():
            return r
        last = r
    return last


def ok(r, what):
    if r.status_code >= 300:
        sys.exit(f"{what} failed {r.status_code}: {r.text[:500]}")
    return r.json() if r.text else {}


def shop_id():
    tok = token()
    if tok.get("shop_id"):
        return tok["shop_id"]
    d = ok(call("GET", f"/users/{tok['user_id']}/shops"), "get shop")
    sid = d.get("shop_id") or (d.get("results") or [{}])[0].get("shop_id")
    tok["shop_id"] = sid
    jsave("tokens.json", tok)
    return sid


def cmd_auth_url(a):
    verifier = base64.urlsafe_b64encode(os.urandom(40)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = pysecrets.token_urlsafe(12)
    jsave("pkce.json", {"verifier": verifier, "state": state, "created": time.time()})
    from urllib.parse import urlencode
    q = urlencode({"response_type": "code", "redirect_uri": REDIRECT, "scope": SCOPES, "client_id": app()["keystring"],
                   "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})
    print("https://www.etsy.com/oauth/connect?" + q)


def cmd_exchange(a):
    p = jload("pkce.json")
    token_request({"grant_type": "authorization_code", "redirect_uri": REDIRECT, "code": a.code, "code_verifier": p["verifier"]})
    os.remove(os.path.join(SECRETS, "pkce.json"))
    print("authorised; shop_id", shop_id())


def cmd_ping(a):
    sid = shop_id()
    d = ok(call("GET", f"/shops/{sid}"), "get shop")
    print(json.dumps({"shop_id": sid, "shop_name": d.get("shop_name"), "currency": d.get("currency_code"),
                      "active_listings": d.get("listing_active_count")}))


def cmd_taxonomy(a):
    d = ok(call("GET", "/seller-taxonomy/nodes"), "taxonomy")
    out = []

    def walk(nodes, path):
        for n in nodes:
            p = path + [n["name"]]
            if a.q.lower() in " > ".join(p).lower():
                out.append((n["id"], " > ".join(p)))
            walk(n.get("children", []), p)
    walk(d.get("results", []), [])
    for i, p in out[:20]:
        print(i, p)


def default_taxonomy():
    d = ok(call("GET", "/seller-taxonomy/nodes"), "taxonomy")
    best = None

    def walk(nodes, path):
        nonlocal best
        for n in nodes:
            p = path + [n["name"].lower()]
            if p[-1] == "digital prints":
                best = n["id"]
            walk(n.get("children", []), p)
    walk(d.get("results", []), [])
    return best


def cmd_publish(a):
    pkg = json.load(open(a.package))
    sid = shop_id()
    tags = [t[:20] for t in pkg.get("tags", [])][:13]
    form = {"quantity": 999, "title": pkg["title"][:140], "description": pkg["description"], "price": float(pkg["price_sek"]),
            "who_made": "i_did", "when_made": "made_to_order", "taxonomy_id": pkg.get("taxonomy_id") or default_taxonomy(),
            "type": "download", "is_supply": "false", "should_auto_renew": "true"}
    data = list(form.items()) + [("tags[]", t) for t in tags] + [("materials[]", m) for m in pkg.get("materials", [])]
    d = ok(call("POST", f"/shops/{sid}/listings", data=data), "create draft listing")
    lid = d["listing_id"]
    for i, img in enumerate(pkg.get("images", [])[:10], 1):
        with open(img, "rb") as f:
            ok(call("POST", f"/shops/{sid}/listings/{lid}/images", files={"image": f}, data={"rank": i}), f"image {img}")
    for i, fp in enumerate(pkg.get("files", [])[:5], 1):
        with open(fp, "rb") as f:
            ok(call("POST", f"/shops/{sid}/listings/{lid}/files", files={"file": f},
                    data={"name": os.path.basename(fp), "rank": i}), f"file {fp}")
    state = "draft"
    if not a.draft:
        r = call("PATCH", f"/shops/{sid}/listings/{lid}", data={"state": "active"})
        state = "active" if r.status_code < 300 else f"draft (activate failed {r.status_code}: {r.text[:200]})"
    print(json.dumps({"listing_id": lid, "url": f"https://www.etsy.com/listing/{lid}", "state": state, "slug": pkg.get("slug")}))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--code"); ap.add_argument("--q", default="digital prints")
    ap.add_argument("--package"); ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    {"auth-url": cmd_auth_url, "exchange": cmd_exchange, "ping": cmd_ping, "taxonomy": cmd_taxonomy,
     "publish": cmd_publish}[a.cmd.replace("_", "-")](a)

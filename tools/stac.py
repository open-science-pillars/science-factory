#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml", "pystac[validation]", "duckdb"]
# ///
"""stac: data described as STAC, for the fresh-data tool, the fence and the registry of openings.

STAC (the SpatioTemporal Asset Catalog, an OGC Community Standard, core
1.1.0) describes data as Items grouped in Collections. Here a description is
static: JSON files (a Collection, and its Items as files or as one NDJSON
file) that live in git and read in a pull request's diff, or a
stac-geoparquet file. Each asset of an Item carries its checksum and size
(the File Info extension, `file:checksum` as a sha2-256 multihash, and
`file:size`). This file reads such descriptions, writes them, validates
them against the STAC JSON schemas that ship inside the pystac package (no
schema is fetched: one that is not there is said to be not validated),
queries them (a collection, a time after a cut-off or inside a window, a
bounding box), asks a STAC API's item search where one is named, and reads
the date column of a Parquet file for the fence. It runs no language model.

DuckDB is the engine, never a store: it runs in this process, with its
extensions neither loaded nor installed on demand and with no file outside
the folders a query names (`enable_external_access` off, the folders
allowed one by one, the configuration locked). It reads stac-geoparquet,
NDJSON and Parquet working data, and writes a stac-geoparquet index that is
generated from the JSON, checksummed beside it, rebuilt at will and never
the record.

Fields of this factory, beside the STAC fields: on a Collection,
`sf:subject` (what the data is about, as key and value) and `sf:releases`
(a release the data grows by: name, cadence, after); on an Item,
`sf:count` (rows or observations), `sf:series`, `sf:site`, `sf:region`,
`sf:release`. They are plain additional fields, not a STAC extension with a
schema of its own.

Commands.

  validate  validate a static catalog, a Collection or Items against the
            schemas shipped with pystac, and with pystac's own reading
  search    the Items of a description or a STAC API that match a query
  index     write the stac-geoparquet index of a description, and its
            checksums beside it
  selftest  the tool tests itself

Usage: stac.py <command> [...]; stac.py selftest
"""
import sys

sys.dont_write_bytecode = True
if __name__ == "__main__" and not (sys.flags.isolated and sys.flags.no_site and "sf-no-bytecode" in str(sys.pycache_prefix)):
    # A clean start, as in the other tools: run again in a Python that reads no PYTHON variable, no user site and no
    # start-up file. What a hostile environment ran before this line has already run (docs/WHAT-IS-ENFORCED.md).
    import os
    _again = [sys.executable, "-I", "-S", "-B", "-X", "pycache_prefix=" + ("/dev/null/sf-no-bytecode" if os.name == "posix" else os.path.join(os.environ.get("TEMP", "."), f"sf-no-bytecode-{os.getpid()}")), os.path.abspath(__file__), *sys.argv[1:]]
    if os.name == "posix":
        os.execv(sys.executable, _again)
    import subprocess
    sys.exit(subprocess.call(_again))
if __name__ == "__main__":
    import os
    import sysconfig
    _env = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
    _lib = ([os.path.join(_env, "lib", f"python{sys.version_info.major}.{sys.version_info.minor}", "site-packages"),
             os.path.join(_env, "Lib", "site-packages")] if os.path.isfile(os.path.join(_env, "pyvenv.cfg"))
            else [sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"]])
    sys.path += [p for p in dict.fromkeys(_lib) if os.path.isdir(p) and p not in sys.path]
if __name__ == "__main__" and not sys.flags.safe_path and sys.path:
    _own = __file__.replace("\\", "/").rpartition("/")[0]
    del sys.path[0]
    sys.path[:] = [p for p in sys.path if p != _own]

import argparse  # noqa: E402
import contextlib  # noqa: E402
import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import shutil  # noqa: E402
import struct  # noqa: E402
import tempfile  # noqa: E402
import urllib.parse  # noqa: E402
import urllib.request  # noqa: E402
from pathlib import Path  # noqa: E402

if "sf" in sys.modules and hasattr(sys.modules["sf"], "Refused"):
    Refused = sys.modules["sf"].Refused  # the study tool's refusal, when the study or exploring tool loaded this file
else:
    class Refused(Exception):
        pass

STAC_VERSION = "1.1.0"
FILE_EXT = "https://stac-extensions.github.io/file/v2.1.0/schema.json"
MULTIHASH_SHA256 = "1220"  # sha2-256, 32 bytes: the multihash prefix the File Info extension's file:checksum carries
GLOBAL = [-180.0, -90.0, 180.0, 90.0]
NDJSON_FROM = 1000  # a description of more Items than this is written as one NDJSON file, not a file for each Item
# what a proposal may read of an Item: the STAC fields that say what exists and where and when, and this factory's own
ITEM_KEYS = ("type", "stac_version", "stac_extensions", "id", "geometry", "bbox", "properties", "links", "assets", "collection")
PROPERTY_KEYS = ("datetime", "start_datetime", "end_datetime", "created", "updated", "title", "description", "license", "providers",
                 "platform", "instruments", "constellation", "mission", "keywords", "version", "deprecated",
                 "sf:count", "sf:series", "sf:site", "sf:region", "sf:release")
ASSET_KEYS = ("href", "type", "title", "description", "roles", "file:checksum", "file:size")
COLLECTION_KEYS = ("type", "stac_version", "stac_extensions", "id", "title", "description", "keywords", "license", "providers",
                   "extent", "summaries", "links", "assets", "item_assets", "sf:subject", "sf:releases", "sf:written_by")
MEDIA = {".csv": "text/csv", ".tsv": "text/tab-separated-values", ".json": "application/json",
         ".parquet": "application/vnd.apache.parquet", ".nc": "application/netcdf", ".txt": "text/plain"}


def sha_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p) -> str | None:
    p = Path(p)
    if not p.is_file():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def multihash(sha_hex: str) -> str:
    return MULTIHASH_SHA256 + sha_hex


def sha_of(checksum) -> str | None:
    """The sha256 a File Info `file:checksum` names, or None when it is not a sha2-256 multihash."""
    c = str(checksum or "").lower()
    return c[4:] if re.fullmatch(MULTIHASH_SHA256 + r"[0-9a-f]{64}", c) else None


def iso(day: dt.date, end: bool = False) -> str:
    return f"{day.isoformat()}T{'23:59:59' if end else '00:00:00'}Z"


def day_of(text) -> dt.date | None:
    """The UTC day of an RFC 3339 date and time (2025-01-31T23:59:59Z), or of a plain date."""
    s = str(text or "").strip()
    if not s:
        return None
    try:
        if "T" not in s and " " not in s:
            return dt.date.fromisoformat(s[:10])
        t = dt.datetime.fromisoformat(s.replace("Z", "+00:00").replace("z", "+00:00"))
        return (t.astimezone(dt.timezone.utc) if t.tzinfo else t).date()
    except ValueError:
        return None


# ---- DuckDB, in this process, locked down ------------------------------------------------------------------
def duck(allowed: list):
    """A DuckDB connection in this process that may read only the folders and files listed: no extension is loaded or
    installed on demand, none from the community or unsigned, nothing outside the list (so no remote file), and the
    configuration locked so that nothing run on it later can change that."""
    try:
        import duckdb
    except ImportError:
        raise Refused("DuckDB is not installed in this tool's environment, so a Parquet file or a stac-geoparquet description cannot "
                      "be read here; nothing was read")
    con = duckdb.connect(config={"autoload_known_extensions": False, "autoinstall_known_extensions": False,
                                 "allow_community_extensions": False, "allow_unsigned_extensions": False})
    dirs = sorted({str(Path(q).resolve()) + "/" for q in allowed if Path(q).is_dir()})
    files = sorted({str(Path(q).resolve()) for q in allowed if Path(q).is_file()})
    if dirs:
        con.execute("SET allowed_directories = " + "[" + ", ".join(sql_text(d) for d in dirs) + "]")
    if files:
        con.execute("SET allowed_paths = " + "[" + ", ".join(sql_text(f) for f in files) + "]")
    con.execute("SET enable_external_access = false")
    con.execute("SET lock_configuration = true")
    return con


def sql_text(s: str) -> str:
    return "'" + str(s).replace("'", "''") + "'"


# ---- reading a description -----------------------------------------------------------------------------------
def _json_file(p: Path):
    try:
        raw = p.read_bytes()
        return json.loads(raw), raw
    except (OSError, ValueError):
        raise Refused(f"{p} is not a JSON file that can be read")


def _local(base: Path, href: str) -> Path:
    """A link of a static catalog, followed only to a file on this machine, relative to the file that names it."""
    h = str(href or "")
    if re.match(r"^[a-z][a-z0-9+.-]*://", h, re.I):
        if h.lower().startswith("file://"):
            return Path(urllib.parse.urlparse(h).path)
        raise Refused(f"the catalog links to {h}: a static description read here is local, and an address on the network is asked only "
                      "as a STAC API (`--catalog https://...`), never followed from a file")
    return Path(os.path.normpath(base.parent / urllib.parse.unquote(h)))


def read_description(path, collection: str | None = None) -> dict:
    """A static STAC description: {"collection": the Collection or None, "items": [Item], "kind", "sha256", "files"}.
    `path` is a Collection's JSON (its Items linked as files with rel `item`, or as one NDJSON file with rel `items`), a
    Catalog's JSON (its one Collection, or the one named), a file of Items as NDJSON, a FeatureCollection, or a
    stac-geoparquet file. The checksum is of every byte read, in the order read."""
    p = Path(os.path.abspath(path))
    if not p.is_file():
        raise Refused(f"{path} names no file of a STAC description")
    digest, files = hashlib.sha256(), []

    def took(f: Path, raw: bytes) -> None:
        digest.update(f.name.encode() + b"\0" + raw + b"\0")
        files.append(str(f))
    if p.suffix.lower() == ".parquet":
        items = read_geoparquet(p)
        took(p, p.read_bytes())
        return {"collection": None, "items": items, "kind": "geoparquet", "sha256": digest.hexdigest(), "files": files}
    if p.suffix.lower() in (".ndjson", ".jsonl"):
        raw = p.read_bytes()
        took(p, raw)
        return {"collection": None, "items": ndjson_items(raw, p), "kind": "ndjson", "sha256": digest.hexdigest(), "files": files}
    obj, raw = _json_file(p)
    took(p, raw)
    if isinstance(obj, dict) and obj.get("type") == "FeatureCollection":
        return {"collection": None, "items": list(obj.get("features") or []), "kind": "item-collection", "sha256": digest.hexdigest(), "files": files}
    if isinstance(obj, dict) and obj.get("type") == "Catalog":
        kids = [_local(p, ln.get("href")) for ln in obj.get("links") or [] if isinstance(ln, dict) and ln.get("rel") == "child"]
        found = []
        for k in kids:
            c, craw = _json_file(k)
            if isinstance(c, dict) and c.get("type") == "Collection" and (collection is None or c.get("id") == collection):
                found.append((k, c, craw))
        if len(found) != 1:
            raise Refused(f"the catalog {p.name} holds {len(found)} collection(s)" + (f" named {collection}" if collection else "")
                          + ": name the Collection's own file, or one collection")
        p, obj, raw = found[0]
        took(p, raw)
    if not isinstance(obj, dict) or obj.get("type") != "Collection":
        raise Refused(f"{p.name} is not a STAC Collection, Catalog, FeatureCollection, NDJSON of Items or stac-geoparquet file")
    items = []
    for ln in obj.get("links") or []:
        if not isinstance(ln, dict):
            continue
        if ln.get("rel") == "item":
            f = _local(p, ln.get("href"))
            it, iraw = _json_file(f)
            took(f, iraw)
            items.append(it)
        elif ln.get("rel") == "items" and str(ln.get("href", "")).lower().endswith((".ndjson", ".jsonl")):
            f = _local(p, ln.get("href"))
            iraw = f.read_bytes() if f.is_file() else b""
            if not f.is_file():
                raise Refused(f"the Collection links its Items to {ln.get('href')}, which is not there")
            took(f, iraw)
            items += ndjson_items(iraw, f)
    return {"collection": obj, "items": items, "kind": "static", "sha256": digest.hexdigest(), "files": files}


def ndjson_items(raw: bytes, where: Path) -> list:
    out = []
    for n, line in enumerate(raw.decode("utf-8", errors="replace").splitlines(), 1):
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                raise Refused(f"line {n} of {where.name} is not JSON: an NDJSON file of Items holds one Item on each line")
    return out


def read_geoparquet(p: Path) -> list:
    """The Items of a stac-geoparquet file, read with DuckDB in this process: the STAC columns are put back as an Item
    (`properties` from the other columns, the geometry from its well-known binary)."""
    con = duck([p])
    try:
        cur = con.execute(f"SELECT * FROM read_parquet({sql_text(str(p.resolve()))})")
        names = [d[0] for d in cur.description]
        rows = cur.fetchall()
    except Exception as e:  # noqa: BLE001  DuckDB's own errors are many kinds
        raise Refused(f"{p.name} could not be read as stac-geoparquet ({type(e).__name__}: {str(e).splitlines()[0][:200]})")
    finally:
        con.close()
    top = {"type", "stac_version", "stac_extensions", "id", "geometry", "bbox", "links", "assets", "collection"}
    items = []
    for row in rows:
        r = dict(zip(names, row))
        it = {k: r[k] for k in top if k in r and r[k] is not None}
        geom = r.get("geometry")
        it["geometry"] = wkb_to_geojson(geom) if isinstance(geom, (bytes, bytearray, memoryview)) else geom
        b = r.get("bbox")
        if isinstance(b, dict):
            it["bbox"] = [b.get("xmin"), b.get("ymin"), b.get("xmax"), b.get("ymax")]
        props = {k: v for k, v in r.items() if k not in top and v is not None}
        for k, v in list(props.items()):
            if isinstance(v, (dt.datetime, dt.date)):
                props[k] = (v.astimezone(dt.timezone.utc) if isinstance(v, dt.datetime) and v.tzinfo else v).strftime("%Y-%m-%dT%H:%M:%SZ") \
                    if isinstance(v, dt.datetime) else v.isoformat()
        props.setdefault("datetime", None)
        it["properties"] = props
        if isinstance(it.get("assets"), str):
            it["assets"] = json.loads(it["assets"])
        if isinstance(it.get("links"), str):
            it["links"] = json.loads(it["links"])
        it["assets"] = {k: {kk: vv for kk, vv in (v or {}).items() if vv is not None} for k, v in (it.get("assets") or {}).items() if v}
        it["links"] = [{kk: vv for kk, vv in ln.items() if vv is not None} for ln in it.get("links") or [] if isinstance(ln, dict)]
        it.setdefault("type", "Feature")
        items.append(it)
    return items


# ---- what an Item says ----------------------------------------------------------------------------------------
def item_span(it: dict) -> tuple | None:
    """(the first day, the last day) an Item covers, in UTC: its start and end, or its one datetime."""
    pr = it.get("properties") or {}
    a, b = day_of(pr.get("start_datetime")), day_of(pr.get("end_datetime"))
    if a and b:
        return a, b
    d = day_of(pr.get("datetime"))
    return (d, d) if d else None


def item_bbox(it: dict) -> list | None:
    b = it.get("bbox")
    if isinstance(b, list) and len(b) >= 4:
        return [float(b[0]), float(b[1]), float(b[-3 if len(b) == 6 else 2]), float(b[-1] if len(b) == 4 else b[4])] if len(b) in (4, 6) else None
    return None


def assets_of(it: dict, base: Path | None = None) -> dict:
    """{asset key: {"href", "sha256", "size"}} from the File Info fields of each asset; the sha256 is None where none is given."""
    out = {}
    for k, a in (it.get("assets") or {}).items():
        if isinstance(a, dict):
            out[k] = {"href": a.get("href"), "sha256": sha_of(a.get("file:checksum")), "size": a.get("file:size")}
    return out


def bbox_meets(a: list | None, b: list | None) -> bool:
    """Do two boxes (west, south, east, north) share any point? A box that crosses the antimeridian has west > east."""
    if a is None or b is None:
        return True

    def spans(w, e):
        return [(w, e)] if w <= e else [(w, 180.0), (-180.0, e)]
    lat = a[1] <= b[3] and b[1] <= a[3]
    lon = any(x0 <= y1 and y0 <= x1 for x0, x1 in spans(a[0], a[2]) for y0, y1 in spans(b[0], b[2]))
    return lat and lon


def parse_bbox(text) -> list | None:
    if text in (None, ""):
        return None
    try:
        parts = [float(x) for x in str(text).split(",")]
    except ValueError:
        parts = []
    if len(parts) != 4 or not (-180 <= parts[0] <= 180 and -180 <= parts[2] <= 180 and -90 <= parts[1] <= parts[3] <= 90):
        raise Refused("`--bbox` is west,south,east,north in degrees (longitude from -180 to 180, latitude from -90 to 90)")
    return parts


def to_metadata(desc: dict, drop=()) -> dict:
    """The description in the fresh-data tool's own form (subject, items, files, releases), with what is STAC's beside it.
    Only the fields a proposal may read are read. A property or an asset field it does not know may hold a measured value
    (cloud cover, a band's statistics), so it is refused unless it is named in `drop`, and then left unread and listed."""
    drop = {d.strip() for d in drop if str(d).strip()}
    col = desc.get("collection") or {}
    items = desc["items"]
    if not items:
        raise Refused("the STAC description holds no Item: a proposal is made from what exists")
    cids = sorted({str(it.get("collection") or col.get("id") or "") for it in items})
    if len(cids) != 1 or not cids[0]:
        raise Refused(f"the Items name {len(cids)} collection(s) ({', '.join(c or 'none' for c in cids)}): a proposal is made from one Collection")
    cid = cids[0]
    for k in col:
        if k not in COLLECTION_KEYS and k not in drop:
            raise Refused(f"the Collection has the field `{k}`, which a proposal does not read: it may hold measured values. Name it with "
                          "`--drop-properties` to leave it unread, and it is listed in the proposal")
    dropped, out_items, files, stac_items, ids = set(), [], {}, {}, set()
    for it in items:
        if not isinstance(it, dict) or it.get("type") != "Feature" or not isinstance(it.get("id"), str) or not it["id"].strip():
            raise Refused("each Item of the description is a STAC Item (a GeoJSON Feature with an `id`)")
        if it["id"] in ids:
            raise Refused(f"the Item `{it['id']}` is given twice")
        ids.add(it["id"])
        for k in it:
            if k not in ITEM_KEYS:
                if k not in drop:
                    raise Refused(f"the Item {it['id']} has the field `{k}`, which a proposal does not read (name it with `--drop-properties` to leave it unread)")
                dropped.add(k)
        props = it.get("properties") or {}
        for k in props:
            if k not in PROPERTY_KEYS:
                if k not in drop:
                    raise Refused(f"the Item {it['id']} has the property `{k}`, which a proposal does not read: it may be a measured value. "
                                  "Name it with `--drop-properties` to leave it unread; the proposal lists it")
                dropped.add(k)
        for name, a in (it.get("assets") or {}).items():
            for k in (a or {}):
                if k not in ASSET_KEYS:
                    if k not in drop:
                        raise Refused(f"the asset `{name}` of the Item {it['id']} has the field `{k}`, which a proposal does not read (it may hold "
                                      "values, such as a band's statistics): name it with `--drop-properties` to leave it unread")
                    dropped.add(k)
        span = item_span(it)
        entry = {"id": it["id"]}
        if span:
            entry["start"], entry["end"] = span[0].isoformat(), span[1].isoformat()
        for k, mk in (("sf:series", "series"), ("sf:site", "site"), ("sf:region", "region"), ("sf:release", "release")):
            if isinstance(props.get(k), str):
                entry[mk] = props[k]
        if isinstance(props.get("sf:count"), int) and not isinstance(props.get("sf:count"), bool) and props["sf:count"] >= 0:
            entry["count"] = props["sf:count"]
        out_items.append(entry)
        assets = assets_of(it)
        stac_items[it["id"]] = {"start": entry.get("start"), "end": entry.get("end"), "bbox": item_bbox(it), "assets": assets}
        for a in assets.values():
            name = Path(urllib.parse.urlparse(str(a["href"] or "")).path).name
            if a["sha256"] and name:
                files.setdefault(name, a["sha256"])
    subject = col.get("sf:subject") if isinstance(col.get("sf:subject"), dict) and col.get("sf:subject") else {"collection": cid}
    meta = {"what": col.get("description") or col.get("title") or f"the STAC collection {cid}", "subject": subject, "items": out_items}
    if files:
        meta["files"] = [{"name": k, "sha256": v} for k, v in sorted(files.items())]
    if isinstance(col.get("sf:releases"), list):
        meta["releases"] = col["sf:releases"]
    return {"meta": meta, "stac": {"collection": cid, "kind": desc["kind"], "sha256": desc["sha256"], "items": stac_items,
                                    "dropped": sorted(dropped)}}


# ---- a query ----------------------------------------------------------------------------------------------------
def query_of(collection: str, start: str | None = None, end: str | None = None, bbox: list | None = None) -> dict:
    """The fresh data as a STAC query: a collection, an interval of time (open at either end), a bounding box or none."""
    return {"collections": [collection], "datetime": f"{iso(dt.date.fromisoformat(start)) if start else '..'}/"
                                                   f"{iso(dt.date.fromisoformat(end), True) if end else '..'}",
            "bbox": bbox}


def interval_of(q: dict) -> tuple:
    a, _, b = str(q.get("datetime") or "../..").partition("/")
    return (day_of(a) if a not in ("", "..") else None), (day_of(b) if b not in ("", "..") else None)


def matches(it: dict, q: dict) -> bool:
    if q.get("collections") and str(it.get("collection") or q.get("_collection") or "") not in q["collections"]:
        return False
    span = item_span(it)
    a, b = interval_of(q)
    if (a or b) and span is None:
        return False
    if a and span[1] < a:
        return False
    if b and span[0] > b:
        return False
    return bbox_meets(item_bbox(it), q.get("bbox")) if q.get("bbox") else True


def search(catalog: str, q: dict, opener=None) -> dict:
    """The Items a catalog lists that match a query: {"items", "asked", "how"}. A local catalog (a static description, NDJSON or
    stac-geoparquet) is read here; NDJSON and stac-geoparquet are filtered with DuckDB. An address (http or https) is a STAC
    API, asked by its item search (POST /search, following `next` links) and nothing else."""
    if re.match(r"^https?://", str(catalog), re.I):
        return api_search(str(catalog), q, opener)
    p = Path(os.path.abspath(catalog))
    if p.suffix.lower() in (".ndjson", ".jsonl", ".parquet") and p.is_file():
        return {"items": duck_search(p, q), "asked": str(p), "how": f"the {p.suffix[1:]} description, filtered with DuckDB in this process"}
    desc = read_description(p, (q.get("collections") or [None])[0])
    cid = (desc.get("collection") or {}).get("id")
    got = [it for it in desc["items"] if matches(it, {**q, "_collection": it.get("collection") or cid})]
    return {"items": got, "asked": str(p), "how": "the static description, read file by file"}


def duck_search(p: Path, q: dict) -> list:
    """Filter a large description with DuckDB: the time and the collection in SQL, the box in Python on what is left."""
    a, b = interval_of(q)
    if p.suffix.lower() == ".parquet":
        rows = [it for it in read_geoparquet(p)]
        return [it for it in rows if matches(it, q)]
    con = duck([p])
    try:
        src = f"read_json({sql_text(str(p.resolve()))}, format='newline_delimited', records=false, columns={{'json': 'JSON'}})"
        where = []
        start = "coalesce(json->>'$.properties.start_datetime', json->>'$.properties.datetime')"
        end = "coalesce(json->>'$.properties.end_datetime', json->>'$.properties.datetime')"
        if a:
            where.append(f"substr({end}, 1, 10) >= {sql_text(a.isoformat())}")
        if b:
            where.append(f"substr({start}, 1, 10) <= {sql_text(b.isoformat())}")
        if q.get("collections"):
            where.append("json->>'$.collection' IN (" + ", ".join(sql_text(c) for c in q["collections"]) + ")")
        sql = f"SELECT json FROM {src}" + (" WHERE " + " AND ".join(where) if where else "")
        rows = [json.loads(r[0]) for r in con.execute(sql).fetchall()]
    except Exception as e:  # noqa: BLE001
        raise Refused(f"{p.name} could not be queried as NDJSON of Items ({type(e).__name__}: {str(e).splitlines()[0][:200]})")
    finally:
        con.close()
    return [it for it in rows if matches(it, q)]


def api_search(url: str, q: dict, opener=None, pages: int = 50) -> dict:
    """A STAC API's item search, asked with POST and its `next` links followed (at most `pages`). Only the search is asked;
    nothing it returns is run or followed elsewhere."""
    base = url.rstrip("/")
    target = base if base.endswith("/search") else base + "/search"
    body = {"collections": q.get("collections"), "datetime": q.get("datetime"), "limit": 100}
    if q.get("bbox"):
        body["bbox"] = q["bbox"]
    host = urllib.parse.urlparse(target).hostname or ""
    if opener is None:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({})) if host in ("127.0.0.1", "localhost", "::1") else urllib.request.build_opener()
    items, asked = [], []
    method, data = "POST", body
    for _ in range(pages):
        req = urllib.request.Request(target, data=json.dumps(data).encode() if method == "POST" else None, method=method,
                                     headers={"Content-Type": "application/json", "Accept": "application/geo+json"})
        asked.append(f"{method} {target}")
        try:
            with opener.open(req, timeout=60) as r:
                page = json.loads(r.read().decode())
        except (OSError, ValueError) as e:
            raise Refused(f"the STAC API at {url} could not be asked ({type(e).__name__}: {str(e)[:200]}): nothing is known about what it "
                          "holds, so nothing is said to be published")
        items += [f for f in page.get("features") or [] if isinstance(f, dict)]
        nxt = next((ln for ln in page.get("links") or [] if isinstance(ln, dict) and ln.get("rel") == "next"), None)
        if not nxt:
            break
        if urllib.parse.urlparse(str(nxt.get("href"))).hostname != host:
            raise Refused("the STAC API's `next` link leaves its own host; it is not followed")
        target, method = str(nxt["href"]), str(nxt.get("method") or "GET").upper()
        data = nxt.get("body") if nxt.get("merge") is False else {**data, **(nxt.get("body") or {})}
    return {"items": [it for it in items if matches(it, q)], "asked": asked, "how": "a STAC API's item search"}


def coverage(items: list) -> dict:
    """What a set of Items covers: how many, the first and last day, and their assets by checksum."""
    spans = [s for s in map(item_span, items) if s]
    return {"items": len(items), "first": min(s[0] for s in spans).isoformat() if spans else None,
            "last": max(s[1] for s in spans).isoformat() if spans else None,
            "ids": sorted(str(it.get("id")) for it in items)}


# ---- writing a description -----------------------------------------------------------------------------------
def geometry_of(bbox: list | None, place: str) -> tuple:
    """(geometry, bbox) of an Item, by the specification's rules: from the data's own positions where it has them (a point,
    or the box they span), the whole globe where the person states it, or no geometry and no bbox."""
    if bbox is not None:
        w, s, e, n = bbox
        if (w, s) == (e, n):
            return {"type": "Point", "coordinates": [w, s]}, [w, s, e, n]
        return {"type": "Polygon", "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]]}, [w, s, e, n]
    if place == "global":
        w, s, e, n = GLOBAL
        return {"type": "Polygon", "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]]}, list(GLOBAL)
    return None, None


def make_item(item_id: str, collection: str, first: dt.date, last: dt.date, asset_path: Path, item_dir: Path, bbox, place: str,
              extra: dict) -> dict:
    geom, box = geometry_of(bbox, place)
    props = {"datetime": None, "start_datetime": iso(first), "end_datetime": iso(last, True), **extra}
    it = {"type": "Feature", "stac_version": STAC_VERSION, "stac_extensions": [FILE_EXT], "id": item_id, "geometry": geom}
    if box is not None:
        it["bbox"] = box
    it.update({"properties": props, "links": [], "collection": collection,
               "assets": {"data": {"href": os.path.relpath(asset_path, item_dir), "type": MEDIA.get(asset_path.suffix.lower(), "application/octet-stream"),
                                   "roles": ["data"], "file:checksum": multihash(sha_file(asset_path)), "file:size": asset_path.stat().st_size}}})
    return it


def write_description(out_dir: Path, collection: dict, items: list, ndjson: bool | None = None, validate: bool = True) -> dict:
    """Write a static description: collection.json, and the Items as items/<id>.json or as items.ndjson. Each Item links to its
    collection and the root; the Collection links to each Item file, or to the NDJSON file with rel `items`. Validated before
    anything is written. Returns {"collection", "items", "ndjson", "validated"}."""
    out_dir = Path(os.path.abspath(out_dir))
    if out_dir.exists() and any(out_dir.iterdir()):
        raise Refused(f"{out_dir} already holds files: a description is written into a new folder and never over one")
    many = len(items) > NDJSON_FROM if ndjson is None else ndjson
    col = dict(collection)
    col["links"] = [{"rel": "root", "href": "./collection.json", "type": "application/json"}]
    for it in items:
        it["links"] = [{"rel": "root", "href": "../collection.json" if not many else "./collection.json", "type": "application/json"},
                       {"rel": "parent", "href": "../collection.json" if not many else "./collection.json", "type": "application/json"},
                       {"rel": "collection", "href": "../collection.json" if not many else "./collection.json", "type": "application/json"}]
    if many:
        col["links"].append({"rel": "items", "href": "./items.ndjson", "type": "application/x-ndjson",
                             "title": "the Items, one on each line (NDJSON is not a form of STAC core)"})
    else:
        col["links"] += [{"rel": "item", "href": f"./items/{it['id']}.json", "type": "application/geo+json"} for it in items]
    found = validate_objects([col] + items) if validate else {"problems": [], "how": "not validated (asked not to, by a self-test that only reads)"}
    if found["problems"]:
        raise Refused("the description is not valid STAC, and nothing was written: " + "; ".join(found["problems"][:4]))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "collection.json").write_text(json.dumps(col, indent=1) + "\n")
    if many:
        with (out_dir / "items.ndjson").open("w") as f:
            for it in items:
                f.write(json.dumps(it, separators=(",", ":")) + "\n")
    else:
        (out_dir / "items").mkdir()
        for it in items:
            (out_dir / "items" / f"{it['id']}.json").write_text(json.dumps(it, indent=1) + "\n")
    back = read_description(out_dir / "collection.json")
    return {"collection": out_dir / "collection.json", "items": len(back["items"]), "ndjson": many, "validated": found["how"],
            "sha256": back["sha256"]}


def rebase_assets(items: list, from_dir: Path, to_dir: Path) -> None:
    """Asset links of Items written from one folder, made relative to another (the NDJSON file sits beside the Collection)."""
    for it in items:
        for a in (it.get("assets") or {}).values():
            a["href"] = os.path.relpath(Path(os.path.normpath(from_dir / a["href"])), to_dir)


# ---- validation, with the schemas pystac ships and nothing fetched -------------------------------------------------------
def validate_objects(objs: list) -> dict:
    """Validate STAC objects (Catalogs, Collections, Items as dicts) against the STAC 1.1.0 JSON schemas and the File Info
    v2.1.0 schema shipped inside the pystac package, and read each with pystac. No schema is fetched: one that is not shipped
    there makes the object `not validated`, and that is said. {"problems", "how"}."""
    try:
        import importlib.resources
        import jsonschema
        import pystac
        import referencing
        from pystac.validation.local_validator import get_local_schema_cache
    except ImportError as e:
        return {"problems": [f"not validated: the validation packages are not installed here ({e.name})"], "how": None}
    store = dict(get_local_schema_cache())
    ext = importlib.resources.files("pystac.extensions") / "json-schema" / "file" / "v2.1.0.json"
    store[FILE_EXT] = json.loads(ext.read_text())

    def retrieve(uri):
        key = uri.rstrip("#")
        if key in store:
            return referencing.Resource.from_contents(store[key], default_specification=referencing.jsonschema.DRAFT7)
        raise referencing.exceptions.NoSuchResource(ref=uri)
    registry = referencing.Registry(retrieve=retrieve)
    problems = []
    for o in objs:
        kind = {"Feature": "item", "Collection": "collection", "Catalog": "catalog"}.get(o.get("type"))
        if kind is None:
            problems.append(f"`{o.get('id')}` is not a STAC Item, Collection or Catalog")
            continue
        core = f"https://schemas.stacspec.org/v{STAC_VERSION}/{kind}-spec/json-schema/{kind}.json"
        for uri in [core] + list(o.get("stac_extensions") or []):
            if uri.rstrip("#") not in store:
                problems.append(f"not validated: `{o.get('id')}` names the schema {uri}, which pystac does not ship and is not fetched here")
                continue
            v = jsonschema.Draft7Validator(store[uri.rstrip("#")], registry=registry)
            try:
                errs = sorted(v.iter_errors(o), key=lambda e: list(e.path))
            except referencing.exceptions.Unresolvable as e:
                problems.append(f"not validated: `{o.get('id')}`: a schema refers to {e}, which is not shipped and is not fetched")
                continue
            problems += [f"`{o.get('id')}` against {uri.rsplit('/', 3)[-3]}: {e.message[:200]}" for e in errs[:3]]
        try:
            {"item": pystac.Item, "collection": pystac.Collection, "catalog": pystac.Catalog}[kind].from_dict(json.loads(json.dumps(o)), migrate=False)
        except Exception as e:  # noqa: BLE001  pystac's errors are many kinds
            problems.append(f"`{o.get('id')}` is not read by pystac: {type(e).__name__}: {str(e)[:200]}")
    return {"problems": problems, "how": f"the STAC {STAC_VERSION} and File Info v2.1.0 JSON schemas shipped in pystac {pystac.__version__}, "
                                         "and pystac's own reading; no schema was fetched"}


# ---- well-known binary, for the generated stac-geoparquet index -------------------------------------------------------
def geojson_to_wkb(g) -> bytes | None:
    if not g:
        return None
    t = g.get("type")
    if t == "Point":
        return struct.pack("<BIdd", 1, 1, *map(float, g["coordinates"][:2]))
    if t == "Polygon":
        rings = g["coordinates"]
        out = struct.pack("<BII", 1, 3, len(rings))
        for ring in rings:
            out += struct.pack("<I", len(ring)) + b"".join(struct.pack("<dd", float(x), float(y)) for x, y, *_ in ring)
        return out
    raise Refused(f"a geometry of type {t} is not written into the index here (a point or a polygon is)")


def wkb_to_geojson(b) -> dict | None:
    b = bytes(b)
    if not b:
        return None
    order = "<" if b[0] == 1 else ">"
    t = struct.unpack(order + "I", b[1:5])[0] % 1000
    if t == 1:
        x, y = struct.unpack(order + "dd", b[5:21])
        return {"type": "Point", "coordinates": [x, y]}
    if t == 3:
        n, at, rings = struct.unpack(order + "I", b[5:9])[0], 9, []
        for _ in range(n):
            k = struct.unpack(order + "I", b[at:at + 4])[0]
            at += 4
            rings.append([list(struct.unpack(order + "dd", b[at + 16 * i:at + 16 * i + 16])) for i in range(k)])
            at += 16 * k
        return {"type": "Polygon", "coordinates": rings}
    return {"type": "Unknown", "wkb_type": t}


def write_index(desc_path, out) -> dict:
    """The stac-geoparquet index of a description: generated from the JSON with DuckDB, never edited, never the record. Its
    checksum, and the checksum of the description it was made from, go beside it (`<out>.json`), so a reader can tell when
    it is stale and rebuild it."""
    desc = read_description(desc_path)
    out = Path(os.path.abspath(out))
    if out.suffix.lower() != ".parquet":
        raise Refused("the index is a .parquet file")
    col = desc.get("collection") or {}
    tmp = Path(tempfile.mkdtemp(prefix="sf-stac-index-"))
    try:
        rows = tmp / "rows.ndjson"
        with rows.open("w") as f:
            for it in desc["items"]:
                pr = it.get("properties") or {}
                b = item_bbox(it)
                f.write(json.dumps({
                    "type": "Feature", "stac_version": it.get("stac_version", STAC_VERSION), "stac_extensions": it.get("stac_extensions") or [],
                    "id": it["id"], "collection": it.get("collection") or col.get("id"),
                    "geometry": (geojson_to_wkb(it.get("geometry")) or b"").hex(),
                    "bbox": {"xmin": b[0], "ymin": b[1], "xmax": b[2], "ymax": b[3]} if b else None,
                    "datetime": pr.get("datetime"), "start_datetime": pr.get("start_datetime"), "end_datetime": pr.get("end_datetime"),
                    "sf:count": pr.get("sf:count"), "sf:series": pr.get("sf:series"), "sf:site": pr.get("sf:site"),
                    "assets": it.get("assets") or {}, "links": it.get("links") or []}) + "\n")
        geo = {"version": "1.1.0", "primary_column": "geometry",
               "columns": {"geometry": {"encoding": "WKB", "geometry_types": ["Point", "Polygon"], "crs": None}}}
        con = duck([tmp, out.parent])
        try:
            con.execute(f"""COPY (SELECT type, stac_version, stac_extensions, id, collection, from_hex(geometry) AS geometry,
                bbox::STRUCT(xmin DOUBLE, ymin DOUBLE, xmax DOUBLE, ymax DOUBLE) AS bbox,
                datetime::VARCHAR::TIMESTAMPTZ AS datetime, start_datetime::VARCHAR::TIMESTAMPTZ AS start_datetime,
                end_datetime::VARCHAR::TIMESTAMPTZ AS end_datetime, "sf:count"::BIGINT AS "sf:count", "sf:series"::VARCHAR AS "sf:series",
                "sf:site"::VARCHAR AS "sf:site", assets, links
                FROM read_json({sql_text(str(rows))}, format='newline_delimited', sample_size=-1)
                ORDER BY id) TO {sql_text(str(out))} (FORMAT parquet, KV_METADATA {{geo: {sql_text(json.dumps(geo))},
                "stac-geoparquet": {sql_text(json.dumps({"version": "1.0.0"}))}}})""")
        finally:
            con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    side = {"says": "generated by tools/stac.py index from the description named here; never edited by hand and never the record: "
                    "the record is the STAC JSON in git. Rebuild it with `uv run tools/stac.py index` when the description changes",
            "generated_from": {"path": os.path.relpath(os.path.abspath(desc_path), out.parent), "sha256": desc["sha256"]},
            "index_sha256": sha_file(out), "items": len(desc["items"])}
    Path(str(out) + ".json").write_text(json.dumps(side, indent=1) + "\n")
    return side


def index_problems(index) -> list:
    """Why an index cannot stand for its description: no checksums beside it, its own bytes changed, or the description it
    was made from has changed since (a stale index is rebuilt, never trusted)."""
    p = Path(os.path.abspath(index))
    side = Path(str(p) + ".json")
    if not side.is_file():
        return [f"{p.name} has no checksums beside it ({side.name}): it is not an index this tool generated"]
    s = json.loads(side.read_text())
    out = []
    if sha_file(p) != s.get("index_sha256"):
        out.append(f"{p.name} is not the file that was generated (its sha256 differs): an index is never edited")
    src = Path(os.path.normpath(p.parent / str((s.get("generated_from") or {}).get("path"))))
    try:
        now = read_description(src)["sha256"]
    except Refused as r:
        return out + [f"the description it was made from cannot be read: {r}"]
    if now != (s.get("generated_from") or {}).get("sha256"):
        out.append(f"the description it was made from ({src.name}) has changed since: rebuild the index (`uv run tools/stac.py index`)")
    return out


# ---- the fence's reading of a Parquet file ------------------------------------------------------------------------
PARQUET_MAGIC = b"PAR1"


def is_parquet(f: Path) -> bool:
    try:
        with Path(f).open("rb") as fh:
            head = fh.read(4)
            fh.seek(-4, 2)
            return head == PARQUET_MAGIC and fh.read(4) == PARQUET_MAGIC
    except OSError:
        return False


def parquet_table(f: Path, date_column, read_date) -> dict:
    """What the fence needs of a Parquet file, read with DuckDB in this process: its columns and types; the row-group
    statistics of each date column (the quick check); and every row's date read in full (the confirmation), as
    (first, last) per distinct value with its count; and the distinct text of each text column, for set-aside names.
    `date_column(name)` says whether a column is named like a time; `read_date(value, column)` is the fence's own reader.
    {"rows", "columns", "date_columns", "row_groups": [{"column", "min", "max"}], "dated": [(first, last, n)],
     "undated": n, "text": {column: [values]}, "sha256"}."""
    f = Path(f).resolve()
    sha = sha_file(f)
    con = duck([f])
    try:
        src = f"read_parquet({sql_text(str(f))})"
        cols = con.execute(f"DESCRIBE SELECT * FROM {src}").fetchall()
        names = [(c[0], str(c[1]).upper()) for c in cols]
        timey = [n for n, t in names if t.startswith(("DATE", "TIMESTAMP")) or date_column(n)]
        rows = con.execute(f"SELECT count(*) FROM {src}").fetchone()[0]
        groups = []
        for c in timey:
            with contextlib.suppress(Exception):
                for rg, mn, mx in con.execute(f"SELECT row_group_id, stats_min, stats_max FROM parquet_metadata({sql_text(str(f))}) "
                                              f"WHERE path_in_schema = {sql_text(c)}").fetchall():
                    groups.append({"column": c, "row_group": rg, "min": mn, "max": mx})
        dated, undated = [], 0
        if timey:
            q = ", ".join(f'"{c}"' for c in timey)
            for row in con.execute(f"SELECT {q}, count(*) FROM {src} GROUP BY ALL").fetchall():
                *vals, n = row
                spans = []
                for c, v in zip(timey, vals):
                    if isinstance(v, dt.datetime):
                        v = (v.astimezone(dt.timezone.utc) if v.tzinfo else v).date()
                    if isinstance(v, dt.date):
                        spans.append((v, v))
                    elif v is not None:
                        got = read_date(v, c)
                        if got:
                            spans.append(got)
                if spans:
                    dated.append((min(a for a, _ in spans), max(b for _, b in spans), n))
                else:
                    undated += n
        else:
            undated = rows
        text = {}
        for n, t in names:
            if t.startswith("VARCHAR") and n not in timey:
                text[n] = [r[0] for r in con.execute(f'SELECT DISTINCT "{n}" FROM {src} WHERE "{n}" IS NOT NULL LIMIT 100000').fetchall()]
    except Refused:
        raise
    except Exception as e:  # noqa: BLE001
        raise Refused(f"{f.name} could not be read as Parquet ({type(e).__name__}: {str(e).splitlines()[0][:200]})")
    finally:
        con.close()
    if sha_file(f) != sha:
        raise Refused(f"{f.name} changed while the fence read it")
    return {"rows": rows, "columns": names, "date_columns": timey, "row_groups": groups, "dated": dated, "undated": undated,
            "text": text, "sha256": sha}


# ---- commands -----------------------------------------------------------------------------------------------------
def cmd_validate(a) -> None:
    desc = read_description(a.path)
    objs = ([desc["collection"]] if desc.get("collection") else []) + desc["items"]
    got = validate_objects(objs)
    for q in got["problems"]:
        print("stac validate:", q)
    print(f"stac validate: {'VALID' if not got['problems'] else 'NOT VALID'} ({len(objs)} object(s); {got['how']})")
    if got["problems"]:
        raise Refused(f"{len(got['problems'])} problem(s)")


def cmd_search(a) -> None:
    q = query_of(a.collection, a.start, a.end, parse_bbox(a.bbox))
    got = search(a.catalog, q)
    print(json.dumps({"query": q, "asked": got["asked"], "how": got["how"], **coverage(got["items"])}, indent=1))


def cmd_index(a) -> None:
    side = write_index(a.description, a.out)
    print(f"index written: {a.out} ({side['items']} Items, sha256 {side['index_sha256'][:16]}), generated from {side['generated_from']['path']} "
          f"(sha256 {side['generated_from']['sha256'][:16]}); it is never the record")


# ---- self-test ----------------------------------------------------------------------------------------------------
def selftest() -> int:
    results = []

    def check(name, ok):
        results.append((name, bool(ok)))

    def refused(fn, *args, **kw):
        try:
            fn(*args, **kw)
        except Refused as r:
            return str(r) or "refused"
        return ""
    tmp = Path(tempfile.mkdtemp(prefix="stac-selftest-")).resolve()
    try:
        data = tmp / "data"
        data.mkdir()
        files = []
        for m in range(1, 4):
            f = data / f"2025-{m:02d}.csv"
            f.write_text("time,lat,lon,value\n" + "".join(f"2025-{m:02d}-{d:02d},{30 + m},{-90 - m},{d / 7:.3f}\n" for d in range(1, 11)))
            files.append(f)
        col = {"type": "Collection", "stac_version": STAC_VERSION, "stac_extensions": [], "id": "toy-gauges", "description": "a toy record",
               "license": "other", "extent": {"spatial": {"bbox": [[-93.0, 31.0, -91.0, 33.0]]},
                                              "temporal": {"interval": [["2025-01-01T00:00:00Z", "2025-03-31T23:59:59Z"]]}},
               "sf:subject": {"record": "toy"}}
        items = [make_item(f"toy-2025-{m:02d}", "toy-gauges", dt.date(2025, m, 1), dt.date(2025, m, 10), files[m - 1], tmp / "cat" / "items",
                           [-90.0 - m, 30.0 + m, -90.0 - m, 30.0 + m], "none", {"sf:count": 10}) for m in range(1, 4)]
        got = write_description(tmp / "cat", col, items)
        check("a Collection and its Items, one for each file, with File Info checksums and sizes, are written as static JSON and "
              "validate against the STAC schemas shipped in pystac, nothing fetched", got["items"] == 3 and not got["ndjson"]
              and "no schema was fetched" in str(got["validated"]) and (tmp / "cat" / "items" / "toy-2025-02.json").is_file())
        desc = read_description(tmp / "cat" / "collection.json")
        a0 = assets_of(desc["items"][0])["data"]
        check("an asset's checksum is the sha256 of its file, as a sha2-256 multihash, and its href is relative",
              a0["sha256"] == sha_file(files[0]) and not str(a0["href"]).startswith("/") and a0["size"] == files[0].stat().st_size)
        bad = json.loads(json.dumps(items[0]))
        bad["properties"].pop("start_datetime")
        check("an Item with no datetime and no start is refused by the schema", validate_objects([bad])["problems"])
        unknown = json.loads(json.dumps(items[0]))
        unknown["stac_extensions"] = ["https://example.invalid/schema.json"]
        check("an extension whose schema is not shipped is said to be not validated, and nothing is fetched",
              any("not validated" in q for q in validate_objects([unknown])["problems"]))
        check("writing over a folder that holds files is refused", "already holds files" in refused(write_description, tmp / "cat", col, items))
        many = write_description(tmp / "nd", col, json.loads(json.dumps(items)), ndjson=True)
        nd = read_description(tmp / "nd" / "collection.json")
        check("many Items are written as one NDJSON file the Collection links to, and read back the same",
              many["ndjson"] and [i["id"] for i in nd["items"]] == [i["id"] for i in desc["items"]])
        meta = to_metadata(desc)
        check("the description reads into the fresh-data tool's form: subject, items with their dates and counts, files by checksum",
              meta["meta"]["subject"] == {"record": "toy"} and meta["meta"]["items"][1] == {"id": "toy-2025-02", "start": "2025-02-01",
                                                                                           "end": "2025-02-10", "count": 10}
              and {f["name"] for f in meta["meta"]["files"]} == {"2025-01.csv", "2025-02.csv", "2025-03.csv"})
        cloudy = json.loads(json.dumps(desc))
        cloudy["items"][0]["properties"]["eo:cloud_cover"] = 12.5
        check("a property a proposal does not read (a measured value, such as cloud cover) is refused, and left unread when named",
              "eo:cloud_cover" in refused(to_metadata, cloudy) and to_metadata(cloudy, drop=["eo:cloud_cover"])["stac"]["dropped"] == ["eo:cloud_cover"])
        q = query_of("toy-gauges", "2025-02-01", None)
        hit = search(str(tmp / "cat" / "collection.json"), q)
        check("a query by collection and a time after a cut-off finds the Items after it", coverage(hit["items"])["ids"] == ["toy-2025-02", "toy-2025-03"])
        box = search(str(tmp / "cat" / "collection.json"), query_of("toy-gauges", None, None, [-92.5, 31.5, -91.5, 32.5]))
        check("a query with a bounding box keeps only the Items that meet it", coverage(box["items"])["ids"] == ["toy-2025-02"])
        ndq = search(str(tmp / "nd" / "items.ndjson"), q)
        check("the same query over NDJSON runs in DuckDB and finds the same Items", coverage(ndq["items"])["ids"] == ["toy-2025-02", "toy-2025-03"]
              and "DuckDB" in ndq["how"])
        side = write_index(tmp / "cat" / "collection.json", tmp / "index.parquet")
        back = read_description(tmp / "index.parquet")
        check("the stac-geoparquet index is generated from the JSON with DuckDB, read back with its geometry and checksums, and its "
              "checksums sit beside it", side["items"] == 3 and [i["id"] for i in back["items"]] == ["toy-2025-01", "toy-2025-02", "toy-2025-03"]
              and back["items"][0]["geometry"]["type"] == "Point" and assets_of(back["items"][0])["data"]["sha256"] == sha_file(files[0])
              and index_problems(tmp / "index.parquet") == [])
        (tmp / "cat" / "items" / "toy-2025-03.json").write_text((tmp / "cat" / "items" / "toy-2025-03.json").read_text().replace('"sf:count": 10', '"sf:count": 9'))
        check("an index whose description changed is stale and said so: it is rebuilt, never trusted", any("has changed since" in q for q in index_problems(tmp / "index.parquet")))
        con = duck([data])
        tries = {}
        for name, sql in (("remote", "SELECT * FROM read_csv('https://example.invalid/x.csv')"), ("install", "INSTALL httpfs"),
                          ("load", "LOAD httpfs"), ("unlock", "SET enable_external_access = true"), ("outside", f"SELECT * FROM read_csv({sql_text(str(tmp / 'index.parquet.json'))})")):
            try:
                con.execute(sql)
                tries[name] = "ran"
            except Exception as e:  # noqa: BLE001
                tries[name] = type(e).__name__
        inside = con.execute(f"SELECT count(*) FROM read_csv({sql_text(str(files[0]))})").fetchone()[0]
        con.close()
        check("the tools' own DuckDB reads what it is given, and cannot read a remote file, install or load an extension, unlock its "
              "settings or read a file outside what it was given", inside == 10 and all(v != "ran" for v in tries.values()))
        pq = tmp / "t.parquet"
        con = duck([tmp])
        con.execute(f"COPY (SELECT DATE '2025-01-01' + i::INTEGER AS day, 'S' || (i % 3) AS site, i * 0.5 AS v FROM range(40) t(i)) TO {sql_text(str(pq))} (FORMAT parquet)")
        con.close()
        tab = parquet_table(pq, lambda n: n == "day", lambda v, c=None: None)
        check("a Parquet file's date column is read by its statistics and in full, with its text columns",
              is_parquet(pq) and tab["rows"] == 40 and tab["date_columns"] == ["day"] and tab["row_groups"] and tab["undated"] == 0
              and max(b for _a, b, _n in tab["dated"]) == dt.date(2025, 2, 9) and sorted(tab["text"]["site"]) == ["S0", "S1", "S2"])

        class Fake:
            def __init__(self, pages):
                self.pages, self.asked = pages, []

            def open(self, req, timeout=None):
                self.asked.append((req.get_method(), req.full_url, json.loads(req.data) if req.data else None))
                return io.BytesIO(json.dumps(self.pages.pop(0)).encode())
        page2 = {"features": [desc["items"][2]], "links": []}
        fake = Fake([{"features": [desc["items"][1]], "links": [{"rel": "next", "href": "https://stac.example.invalid/search?page=2", "method": "GET"}]}, page2])
        api = api_search("https://stac.example.invalid", q, opener=fake)
        check("a STAC API is asked by its item search, with the query in the body, and its next link followed",
              coverage(api["items"])["ids"] == ["toy-2025-02", "toy-2025-03"] and fake.asked[0][0] == "POST"
              and fake.asked[0][2]["collections"] == ["toy-gauges"] and fake.asked[1][0] == "GET")
        away = Fake([{"features": [], "links": [{"rel": "next", "href": "https://elsewhere.invalid/search"}]}])
        check("a next link that leaves the API's host is not followed", "leaves its own host" in refused(api_search, "https://stac.example.invalid", q, away))
        check("a static description that links to the network is refused, not followed", "is local" in refused(_local, tmp / "c.json", "https://x.invalid/i.json"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    for name, ok in results:
        print(("PASS  " if ok else "FAIL  ") + name)
    good = all(ok for _, ok in results)
    print(f"selftest: {'PASS' if good else 'FAIL'} ({sum(ok for _, ok in results)} of {len(results)})")
    return 0 if good else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter, allow_abbrev=False)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("validate", allow_abbrev=False, help="validate a static description against the schemas shipped with pystac")
    p.add_argument("path", help="a Collection's or Catalog's JSON, NDJSON of Items, or a stac-geoparquet file")
    p.set_defaults(fn=cmd_validate)
    p = sub.add_parser("search", allow_abbrev=False, help="the Items of a description or a STAC API that match a query")
    p.add_argument("--catalog", required=True, help="a static description (path) or a STAC API (https address)")
    p.add_argument("--collection", required=True)
    p.add_argument("--start", default=None, help="the first day, YYYY-MM-DD")
    p.add_argument("--end", default=None, help="the last day, YYYY-MM-DD")
    p.add_argument("--bbox", default=None, help="west,south,east,north")
    p.set_defaults(fn=cmd_search)
    p = sub.add_parser("index", allow_abbrev=False, help="write the stac-geoparquet index of a description")
    p.add_argument("--description", required=True)
    p.add_argument("--out", required=True, help="the index, a .parquet file; its checksums go beside it")
    p.set_defaults(fn=cmd_index)
    sub.add_parser("selftest", allow_abbrev=False, help="the tool tests itself")
    return ap


def main() -> int:
    a = build_parser().parse_args()
    try:
        if a.cmd == "selftest":
            return selftest()
        a.fn(a)
    except Refused as r:
        print(f"REFUSED: {r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())

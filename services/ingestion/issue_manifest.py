"""Resolve and download specifications selected from a TIPO issue manifest."""

import hashlib
import re
import time
from ftplib import all_errors
from pathlib import Path
from tempfile import NamedTemporaryFile

from services.ingestion.artifacts import MAX_GAZETTE_XML_BYTES, MAX_XML_BYTES
from services.ingestion.download import download_ftps_xml
from services.ingestion.patentpub import parse_xml

HOST = "ftps://ftp.tipo.gov.tw"
MANIFEST_URL = re.compile(
    rf"{re.escape(HOST)}/InventionPubXML/([0-9]{{3}})/InventionPubXML_([0-9]{{6}})/index_all\.xml"
)
GRANT_MANIFEST_URL = re.compile(
    rf"{re.escape(HOST)}/PatentIsuRegSpecXMLA/([0-9]{{3}})/PatentIsuRegSpecXMLA_([0-9]{{6}})/index_all\.xml"
)


def resolve_spec_urls(data, manifest_url, issue, publications, *, grant=False):
    match = (GRANT_MANIFEST_URL if grant else MANIFEST_URL).fullmatch(manifest_url)
    if not match or match[2] != issue:
        raise ValueError("Manifest URL must point to the requested TIPO issue")
    root = parse_xml(data, size_limit=MAX_GAZETTE_XML_BYTES if grant else MAX_XML_BYTES)
    root_name, item_name, number_attribute, archive = (
        ("tw-patent-grants", "tw-patent-grant", "certificate-number", "PatentPubXML")
        if grant
        else (
            "tw-patent-applications",
            "tw-patent-application",
            "publication-number",
            "InventionPubXML",
        )
    )
    if root.tag != root_name or root.get("total-count") != str(len(root)):
        raise ValueError("Invalid TIPO issue manifest")

    urls = {}
    used_paths = set()
    directory = f"/{archive}_{issue}/"
    for record in root:
        if record.tag != item_name:
            raise ValueError("Unexpected record in TIPO issue manifest")
        number = record.get(number_attribute)
        if number not in publications:
            continue
        node = record.find("specification-files")
        relative = node.get("xml-file", "") if node is not None else ""
        file_pattern = (
            rf"{directory}[0-9]+{number}/{publications[number]}-[A-Za-z0-9_-]+\.xml"
        )
        if (
            not re.fullmatch(file_pattern, relative)
            or number in urls
            or relative in used_paths
        ):
            raise ValueError(
                "Invalid or duplicate specification link in TIPO issue manifest"
            )
        used_paths.add(relative)
        urls[number] = f"{HOST}/{archive}/{match[1]}{relative}"
    if urls.keys() != publications.keys():
        raise ValueError("TIPO issue manifest does not cover the selected publications")
    return urls


def fetch_cached(url: str, cache: Path, *, cache_only: bool) -> Path:
    key = hashlib.sha256(url.encode()).hexdigest()
    path = cache / key
    if path.exists():
        with path.open("rb") as stream:
            data = stream.read(MAX_XML_BYTES + 1)
        if len(data) > MAX_XML_BYTES:
            raise ValueError("Cached XML exceeds the size limit")
        return path

    if cache_only:
        raise FileNotFoundError("No cached TIPO XML; run --fetch-only on the host")
    data = download_ftps_xml(url)
    time.sleep(1)
    with NamedTemporaryFile(dir=cache, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)
    return path


def fetch_specifications(urls, cache: Path, *, cache_only: bool = False):
    payloads = {}
    failures = {}
    for number, url in urls.items():
        try:
            payloads[number] = fetch_cached(url, cache, cache_only=cache_only)
        except (*all_errors, ValueError) as error:
            failures[number] = f"{type(error).__name__}: {error}"
            if not cache_only:
                time.sleep(1)
    return payloads, failures

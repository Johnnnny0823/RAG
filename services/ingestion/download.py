"""Retrieve a TIPO issue index and optionally one explicitly selected specification."""

import argparse
import logging
import re
import socket
import ssl
from ftplib import FTP, FTP_TLS, error_temp
from pathlib import Path
from time import sleep
from urllib.parse import urlsplit
from urllib.request import urlopen

from services.ingestion.artifacts import MAX_GAZETTE_XML_BYTES, MAX_XML_BYTES
from services.ingestion.patentpub import APPLICATION_NUMBER_PATTERN

logger = logging.getLogger(__name__)
INDEX_URL = "https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10"
GRANT_INDEX_URL = "https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S01"
LEGAL_INDEX_URL = "https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/P10"
ARCHIVES = {
    "publication": "InventionPubXML",
    "grant": "PatentIsuRegSpecXMLA",
    "legal": "PatentIsuModXML",
}
SPEC_PATH = re.compile(
    r"/(?:InventionPubXML|PatentIsuRegSpecXMLA)/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_-]+\.xml"
    rf"|/PatentPubXML/[0-9]{{3}}/PatentPubXML_[0-9]{{6}}/(?:[0-9]+[IM][0-9]+/[0-9]{{9}}|[0-9]+D[0-9]+/{APPLICATION_NUMBER_PATTERN})-[A-Za-z0-9_-]+\.xml"
)
EVENT_PATH = re.compile(
    r"/PatentIsuModXML/[0-9]{3}/PatentIsuModXML_[0-9]{6}/(?:index|sud08|sud24)\.xml"
)
GAZETTE_PATH = re.compile(
    r"/(?:PatentIsuRegSpecXMLA/[0-9]{3}/PatentIsuRegSpecXMLA_[0-9]{6}/index(?:_all)?"
    r"|PatentPubRegXMLB/[0-9]{3}/PatentPubRegXMLB_[0-9]{6}/pubinvention"
    r"|PatentIsuRegSpecXMLB/[0-9]{3}/PatentIsuRegSpecXMLB_[0-9]{6}/patent)\.xml"
)


# The server sends its leaf and "TWCA SSL Certification Authority" but omits this
# cross-certificate, which links them to the "TWCA CYBER Root CA" root. Windows fetches
# it on demand; OpenSSL does not, and fails to verify the server without it.
CROSS_CERTIFICATE = Path(__file__).with_name("twca_cyber_root_ca_g3.pem")


def tls_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    # The bundled certificate may only bridge to a root the system already trusts.
    context.verify_flags &= ~ssl.VERIFY_X509_PARTIAL_CHAIN
    context.load_verify_locations(cafile=CROSS_CERTIFICATE)
    return context


class TIPOTransfer(FTP_TLS):
    def connect_implicit(self):
        self.host, self.port = "ftp.tipo.gov.tw", 990
        with socket.create_connection(
            (self.host, self.port), self.timeout
        ) as connection:
            self.sock = self.context.wrap_socket(connection, server_hostname=self.host)
        self.af = self.sock.family
        self.file = self.sock.makefile("r", encoding=self.encoding)
        self.getresp()

    def ntransfercmd(self, cmd, rest=None):
        connection, size = FTP.ntransfercmd(self, cmd, rest)
        try:
            protected = self.context.wrap_socket(
                connection, server_hostname=self.host, session=self.sock.session
            )
        except OSError:
            connection.close()
            raise
        return protected, size


def download_ftps_xml(url: str) -> bytes:
    parsed = urlsplit(url)
    gazette = GAZETTE_PATH.fullmatch(parsed.path)
    if (
        parsed.scheme != "ftps"
        or parsed.netloc not in {"ftp.tipo.gov.tw", "ftp.tipo.gov.tw:990"}
        or parsed.query
        or parsed.fragment
        or not (
            gazette
            or SPEC_PATH.fullmatch(parsed.path)
            or EVENT_PATH.fullmatch(parsed.path)
        )
        or any(part in {".", ".."} for part in parsed.path.split("/"))
    ):
        raise ValueError("Expected a TIPO patent XML FTPS URL")
    size_limit = MAX_GAZETTE_XML_BYTES if gazette else MAX_XML_BYTES
    return download_verified_path(parsed.path, size_limit)


def download_verified_path(path: str, size_limit: int) -> bytes:
    """Transfer a path that the calling importer has already validated."""
    context = tls_context()
    # A busy passive listener can temporarily refuse otherwise valid transfers.
    for delay in (15, 45):
        try:
            return _transfer_xml(path, context, size_limit)
        except error_temp as error:
            if str(error)[:3] != "425":
                raise
            logger.warning(
                "TIPO FTPS data channel unavailable (425); retry in %ds", delay
            )
            sleep(delay)
    return _transfer_xml(path, context, size_limit)


def _transfer_xml(path: str, context: ssl.SSLContext, size_limit: int) -> bytes:
    payload = bytearray()

    def append(chunk: bytes) -> None:
        if len(payload) + len(chunk) > size_limit:
            raise ValueError("TIPO specification exceeds the XML size limit")
        payload.extend(chunk)

    with TIPOTransfer(timeout=30, context=context) as ftp:
        ftp.connect_implicit()
        ftp.login()
        ftp.prot_p()
        ftp.voidcmd("TYPE I")
        size = ftp.size(path)
        if size is None or not 0 < size <= size_limit:
            raise ValueError("Unexpected TIPO specification size")
        response = ftp.retrbinary(f"RETR {path}", append)
        if not response.startswith("226 ") or len(payload) != size:
            raise ValueError("TIPO did not confirm a complete specification transfer")
    return bytes(payload)


def download_publication_index() -> bytes:
    return _download_https_index(INDEX_URL, MAX_XML_BYTES)


def download_grant_index() -> bytes:
    return _download_https_index(GRANT_INDEX_URL, MAX_GAZETTE_XML_BYTES)


def download_legal_index() -> bytes:
    return _download_https_index(LEGAL_INDEX_URL, MAX_XML_BYTES)


def list_archive_issues(stage: str, year: str) -> list[str]:
    if not re.fullmatch(r"[0-9]{3}", year):
        raise ValueError("Expected a three-digit ROC archive year")
    folder = ARCHIVES[stage]
    directory = re.compile(rf"{folder}_([0-9]{{6}})")
    issues = []
    lines = 0

    def collect(line: str) -> None:
        nonlocal lines
        lines += 1
        if lines > 512:
            raise ValueError("TIPO archive listing exceeds its size limit")
        fields = line.split(maxsplit=8)
        if len(fields) == 9 and fields[0].startswith("d"):
            if match := directory.fullmatch(fields[8]):
                issues.append(match[1])

    with TIPOTransfer(timeout=30, context=tls_context()) as ftp:
        ftp.connect_implicit()
        ftp.login()
        ftp.prot_p()
        ftp.cwd(f"/{folder}/{year}")
        response = ftp.retrlines("LIST", collect)
    if not response.startswith("226 ") or not issues or len(issues) != len(set(issues)):
        raise ValueError("TIPO did not return a complete archive listing")
    return sorted(issues)


def _download_https_index(url: str, size_limit: int) -> bytes:
    with urlopen(url, timeout=60) as response:
        if response.geturl() != url:
            raise ValueError("Unexpected final URL for the TIPO issue index")
        payload = response.read(size_limit + 1)
    if not payload or len(payload) > size_limit:
        raise ValueError("Unexpected TIPO issue index size")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-out", type=Path)
    index_source = parser.add_mutually_exclusive_group()
    index_source.add_argument(
        "--index-url", help="Official archived issue index FTPS URL"
    )
    index_source.add_argument(
        "--latest-grants", action="store_true", help="Use the official S01 index"
    )
    parser.add_argument("--spec-url")
    parser.add_argument("--spec-out", type=Path)
    args = parser.parse_args()
    if (
        ((args.index_url or args.latest_grants) and not args.index_out)
        or bool(args.spec_url) != bool(args.spec_out)
        or not (args.index_out or args.spec_out)
    ):
        parser.error("Provide --index-out or both --spec-url and --spec-out")
    if args.index_out:
        if args.index_url:
            payload = download_ftps_xml(args.index_url)
        elif args.latest_grants:
            payload = download_grant_index()
        else:
            payload = download_publication_index()
        with args.index_out.open("xb") as stream:
            stream.write(payload)
    if args.spec_out:
        payload = download_ftps_xml(args.spec_url)
        with args.spec_out.open("xb") as stream:
            stream.write(payload)


if __name__ == "__main__":
    main()

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

logger = logging.getLogger(__name__)
INDEX_URL = "https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10"
SPEC_PATH = re.compile(
    r"/(?:InventionPubXML|PatentIsuRegSpecXMLA)/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_-]+\.xml"
)
EVENT_PATH = re.compile(
    r"/PatentIsuModXML/[0-9]{3}/PatentIsuModXML_[0-9]{6}/sud(?:08|24)\.xml"
)
GAZETTE_PATH = re.compile(
    r"/(?:PatentIsuRegSpecXMLA/[0-9]{3}/PatentIsuRegSpecXMLA_[0-9]{6}/index"
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
    context = tls_context()
    size_limit = MAX_GAZETTE_XML_BYTES if gazette else MAX_XML_BYTES
    # A busy passive listener can temporarily refuse otherwise valid transfers.
    for delay in (15, 45):
        try:
            return _transfer_xml(parsed.path, context, size_limit)
        except error_temp as error:
            if str(error)[:3] != "425":
                raise
            logger.warning(
                "TIPO FTPS data channel unavailable (425); retry in %ds", delay
            )
            sleep(delay)
    return _transfer_xml(parsed.path, context, size_limit)


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
    with urlopen(INDEX_URL, timeout=60) as response:
        if response.geturl() != INDEX_URL:
            raise ValueError("Unexpected final URL for the TIPO publication index")
        payload = response.read(MAX_XML_BYTES + 1)
    if not payload or len(payload) > MAX_XML_BYTES:
        raise ValueError("Unexpected TIPO publication index size")
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-out", type=Path)
    parser.add_argument("--index-url", help="Official archived issue index FTPS URL")
    parser.add_argument("--spec-url")
    parser.add_argument("--spec-out", type=Path)
    args = parser.parse_args()
    if (
        (args.index_url and not args.index_out)
        or bool(args.spec_url) != bool(args.spec_out)
        or not (args.index_out or args.spec_out)
    ):
        parser.error("Provide --index-out or both --spec-url and --spec-out")
    if args.index_out:
        payload = (
            download_ftps_xml(args.index_url)
            if args.index_url
            else download_publication_index()
        )
        with args.index_out.open("xb") as stream:
            stream.write(payload)
    if args.spec_out:
        payload = download_ftps_xml(args.spec_url)
        with args.spec_out.open("xb") as stream:
            stream.write(payload)


if __name__ == "__main__":
    main()

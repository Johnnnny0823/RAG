"""Retrieve a TIPO issue index and optionally one explicitly selected specification."""

import argparse
import re
import socket
import ssl
from ftplib import FTP, FTP_TLS
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import urlopen

from services.ingestion.artifacts import MAX_XML_BYTES

INDEX_URL = "https://cloud.tipo.gov.tw/S220/opdata/api/gazettes/S10"
SPEC_PATH = re.compile(r"/InventionPubXML/(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_-]+\.xml")


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
    if (
        parsed.scheme != "ftps"
        or parsed.netloc not in {"ftp.tipo.gov.tw", "ftp.tipo.gov.tw:990"}
        or parsed.query
        or parsed.fragment
        or not SPEC_PATH.fullmatch(parsed.path)
        or any(part in {".", ".."} for part in parsed.path.split("/"))
    ):
        raise ValueError("Expected a TIPO InventionPubXML FTPS URL")
    payload = bytearray()

    def append(chunk: bytes) -> None:
        if len(payload) + len(chunk) > MAX_XML_BYTES:
            raise ValueError("TIPO specification exceeds the XML size limit")
        payload.extend(chunk)

    with TIPOTransfer(timeout=30, context=ssl.create_default_context()) as ftp:
        ftp.connect_implicit()
        ftp.login()
        ftp.prot_p()
        ftp.voidcmd("TYPE I")
        size = ftp.size(parsed.path)
        if size is None or not 0 < size <= MAX_XML_BYTES:
            raise ValueError("Unexpected TIPO specification size")
        response = ftp.retrbinary(f"RETR {parsed.path}", append)
        if not response.startswith("226 ") or len(payload) != size:
            raise ValueError("TIPO did not confirm a complete specification transfer")
    return bytes(payload)


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
        if args.index_url:
            payload = download_ftps_xml(args.index_url)
        else:
            with urlopen(INDEX_URL, timeout=60) as response:
                payload = response.read(MAX_XML_BYTES + 1)
        if len(payload) > MAX_XML_BYTES:
            raise ValueError("TIPO index exceeds the XML size limit")
        with args.index_out.open("xb") as stream:
            stream.write(payload)
    if args.spec_out:
        payload = download_ftps_xml(args.spec_url)
        with args.spec_out.open("xb") as stream:
            stream.write(payload)


if __name__ == "__main__":
    main()

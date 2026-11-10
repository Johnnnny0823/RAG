import hashlib
import ssl

from services.ingestion.download import CROSS_CERTIFICATE, tls_context


def test_tipo_tls_context_adds_only_the_reviewed_bridge_certificate():
    der = ssl.PEM_cert_to_DER_cert(CROSS_CERTIFICATE.read_text(encoding="ascii"))
    assert (
        hashlib.sha256(der).hexdigest()
        == "6e63068c8a6b422effa159e983a1a682443848ef8386fee4504aac5608998241"
    )

    context = tls_context()
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname
    assert not context.verify_flags & ssl.VERIFY_X509_PARTIAL_CHAIN

"""Tests for SSRF validation, PII stripping, error sanitization, and retry logic."""

from __future__ import annotations

import pytest
from zernio_mcp.client import validate_url_for_ssrf, SSRFError, strip_pii


class TestSSRFValidation:
    def test_rejects_http_scheme(self):
        with pytest.raises(SSRFError, match="Only HTTPS"):
            validate_url_for_ssrf("http://example.com/image.jpg")

    def test_rejects_file_scheme(self):
        with pytest.raises(SSRFError, match="Only HTTPS"):
            validate_url_for_ssrf("file:///etc/passwd")

    def test_rejects_ftp_scheme(self):
        with pytest.raises(SSRFError, match="Only HTTPS"):
            validate_url_for_ssrf("ftp://example.com/file")

    def test_rejects_no_hostname(self):
        with pytest.raises(SSRFError):
            validate_url_for_ssrf("https://")

    def test_rejects_private_ip_10(self):
        with pytest.raises(SSRFError, match="non-public"):
            validate_url_for_ssrf("https://10.0.0.1/image.jpg")

    def test_rejects_private_ip_192(self):
        with pytest.raises(SSRFError, match="non-public"):
            validate_url_for_ssrf("https://192.168.1.1/image.jpg")

    def test_rejects_private_ip_172(self):
        with pytest.raises(SSRFError, match="non-public"):
            validate_url_for_ssrf("https://172.16.0.1/image.jpg")

    def test_rejects_loopback(self):
        with pytest.raises(SSRFError, match="non-public"):
            validate_url_for_ssrf("https://127.0.0.1/image.jpg")

    def test_rejects_link_local(self):
        with pytest.raises(SSRFError, match="non-public"):
            validate_url_for_ssrf("https://169.254.169.254/latest/meta-data/")

    def test_accepts_public_https(self):
        # Should not raise
        validate_url_for_ssrf("https://images.unsplash.com/photo.jpg")

    def test_rejects_unresolvable_host(self):
        with pytest.raises(SSRFError, match="Cannot resolve"):
            validate_url_for_ssrf("https://this-domain-does-not-exist-zxcvbnm.com/x")


class TestPIIStripping:
    def test_strips_email(self):
        result = strip_pii({"_id": "1", "platform": "twitter", "email": "user@example.com"})
        assert "email" not in result
        assert result["_id"] == "1"

    def test_strips_phone(self):
        result = strip_pii({"_id": "1", "phone": "+491234567", "phoneNumber": "+491234567"})
        assert "phone" not in result
        assert "phoneNumber" not in result

    def test_keeps_non_pii_fields(self):
        data = {"_id": "1", "platform": "instagram", "username": "test", "displayName": "Test"}
        result = strip_pii(data)
        assert result == data

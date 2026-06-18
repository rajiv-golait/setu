"""Phone matching helpers for Supabase admin."""
from app.services.supabase_admin import phone_match_key, phones_match


def test_phone_match_key_indian_formats():
    assert phone_match_key("+919699106244") == "9699106244"
    assert phone_match_key("919699106244") == "9699106244"
    assert phone_match_key("9699106244") == "9699106244"


def test_phones_match_across_formats():
    assert phones_match("+919699106244", "9699106244")
    assert phones_match("919699106244", "+919699106244")
    assert not phones_match("+919876543210", "9699106244")

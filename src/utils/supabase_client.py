import os
from typing import Optional
from dotenv import load_dotenv

# Supabase v2 python client
try:
    from supabase import create_client, Client
except Exception:
    create_client = None
    Client = None

_load_done = False
_client: Optional["Client"] = None


def get_supabase() -> "Client":
    """Singleton Supabase client initialized from environment variables.

    Requires SUPABASE_URL and SUPABASE_ANON_KEY. Optionally SUPABASE_BUCKET.
    """
    global _load_done, _client
    if not _load_done:
        load_dotenv(override=False)
        _load_done = True

    if _client is not None:
        return _client

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_ANON_KEY in environment/.env")
    if create_client is None:
        raise RuntimeError("Supabase client not installed. Add 'supabase' to requirements and install.")

    _client = create_client(url, key)
    return _client


def get_bucket_name() -> str:
    return os.environ.get("SUPABASE_BUCKET", "boards")

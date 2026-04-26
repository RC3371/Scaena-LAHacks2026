import os


_client = None


def _mongo_client_options() -> dict:
    options = {
        "serverSelectionTimeoutMS": 1200,
        "connectTimeoutMS": 1200,
    }
    try:
        import certifi

        options["tlsCAFile"] = certifi.where()
    except Exception:
        pass
    return options


def get_db():
    global _client

    uri = (os.getenv("MONGODB_URI") or os.getenv("MONGO_URI") or "").strip()
    if not uri:
        return None

    try:
        from pymongo import MongoClient
    except ImportError:
        return None

    if _client is None:
        try:
            _client = MongoClient(uri, **_mongo_client_options())
        except Exception:
            return None

    db_name = os.getenv("MONGODB_DB_NAME") or os.getenv("MONGODB_DB") or "scaena"
    return _client[db_name]

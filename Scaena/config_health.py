import os


_PLACEHOLDER_VALUES = {
    "",
    "placeholder",
    "your_asi1_api_key_here",
    "your_agentverse_api_key_here",
    "your_gemini_api_key_here",
    "your_google_search_api_key_here",
    "your_programmable_search_engine_id_here",
    "your_eventbrite_private_token_here",
    "your_google_client_id_here",
    "your_google_client_secret_here",
}


def _raw(name: str) -> str:
    return (os.getenv(name) or "").strip()


def _is_configured(name: str) -> bool:
    value = _raw(name)
    lowered = value.lower()
    return bool(value) and lowered not in _PLACEHOLDER_VALUES and not lowered.startswith("your_")


def _bool_env(name: str, default: bool = False) -> bool:
    value = _raw(name)
    if not value:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def _line(status: str, label: str, detail: str = "") -> str:
    suffix = f" - {detail}" if detail else ""
    return f"  {status} {label}{suffix}"


def config_health_lines(component: str = "app") -> list[str]:
    lines = [f"\nScaena config health [{component}]:"]

    asi_live = _is_configured("ASI1_API_KEY")
    lines.append(_line("[OK]" if asi_live else "[WARN]", "ASI1_API_KEY", "live ASI-1 enabled" if asi_live else "missing, agents use simulation/mock logic"))
    lines.append(_line("[OK]" if _is_configured("AGENTVERSE_API_KEY") else "[WARN]", "AGENTVERSE_API_KEY", "set" if _is_configured("AGENTVERSE_API_KEY") else "missing, Agentverse registration disabled"))

    gemini = _is_configured("GEMINI_API_KEY") or _is_configured("GOOGLE_API_KEY")
    google_search_key = _is_configured("GOOGLE_SEARCH_API_KEY") or _is_configured("GOOGLE_API_KEY") or _is_configured("GEMINI_API_KEY")
    google_search_cx = _is_configured("GOOGLE_SEARCH_ENGINE_ID") or _is_configured("GOOGLE_CSE_ID") or _is_configured("GOOGLE_CUSTOM_SEARCH_CX")
    eventbrite = _is_configured("EVENTBRITE_API_TOKEN") or _is_configured("EVENTBRITE_API_KEY")
    live_research = gemini or (google_search_key and google_search_cx) or eventbrite

    lines.append(_line("[OK]" if live_research else "[WARN]", "Live market research", "at least one live source configured" if live_research else "no live source keys, falls back to generated research"))
    lines.append(_line("[OK]" if gemini else "[INFO]", "Gemini grounding", "enabled" if gemini else "not configured"))
    if google_search_key != google_search_cx:
        lines.append(_line("[WARN]", "Google Programmable Search", "partial config, set GOOGLE_SEARCH_ENGINE_ID and either GOOGLE_SEARCH_API_KEY or GOOGLE_API_KEY"))
    else:
        lines.append(_line("[OK]" if google_search_key else "[INFO]", "Google Programmable Search", "enabled" if google_search_key else "not configured"))
    lines.append(_line("[OK]" if eventbrite else "[INFO]", "Eventbrite API", "enabled" if eventbrite else "optional, not configured"))

    gmail_client = _is_configured("GOOGLE_CLIENT_ID")
    gmail_secret = _is_configured("GOOGLE_CLIENT_SECRET")
    if gmail_client and gmail_secret:
        lines.append(_line("[OK]", "Gmail OAuth", "configured"))
    elif gmail_client or gmail_secret:
        lines.append(_line("[WARN]", "Gmail OAuth", "partial config, set both GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET"))
    else:
        lines.append(_line("[WARN]", "Gmail OAuth", "missing, connect/send/sync disabled"))

    live_sends = _bool_env("GMAIL_LIVE_SENDS", False)
    lines.append(_line("[WARN]" if live_sends else "[INFO]", "GMAIL_LIVE_SENDS", "true, real emails can send" if live_sends else "false, Gmail sends are dry-run"))
    lines.append(_line("[OK]" if _is_configured("GMAIL_TEST_RECIPIENT") else "[INFO]", "GMAIL_TEST_RECIPIENT", "set, all sends route to test inbox" if _is_configured("GMAIL_TEST_RECIPIENT") else "not set"))
    lines.append(_line("[OK]" if _is_configured("EMAIL_ALLOWLIST") else "[INFO]", "EMAIL_ALLOWLIST", "set" if _is_configured("EMAIL_ALLOWLIST") else "not set"))
    if live_sends and not _is_configured("GMAIL_TEST_RECIPIENT") and not _is_configured("EMAIL_ALLOWLIST"):
        lines.append(_line("[WARN]", "Email safety", "live sends enabled without GMAIL_TEST_RECIPIENT or EMAIL_ALLOWLIST"))

    lines.append(_line("[OK]" if _is_configured("DATABASE_URL") else "[WARN]", "DATABASE_URL", "set" if _is_configured("DATABASE_URL") else "missing, default SQLite path will be used"))
    lines.append(_line("[INFO]", "SCAENA_SEED_DEMO", "true, demo fixture may load" if _bool_env("SCAENA_SEED_DEMO", False) else "false, demo fixture skipped"))

    return lines


def print_config_health(component: str = "app"):
    for line in config_health_lines(component):
        print(line, flush=True)


def config_health_text(component: str = "app") -> str:
    return "\n".join(config_health_lines(component))

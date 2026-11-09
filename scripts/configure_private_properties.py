#!/usr/bin/env python3
"""Write Telegram API credentials into a private.properties file without logging secrets."""
import os
import pathlib
import re
import sys

template = pathlib.Path(sys.argv[1])
destination = pathlib.Path(sys.argv[2])
api_id = os.environ.get("TG_API_ID", "").strip()
api_hash = os.environ.get("TG_API_HASH", "").strip()

if not api_id.isdigit():
    raise SystemExit("TG_API_ID secret is missing or is not numeric.")
if not re.fullmatch(r"[0-9a-fA-F]{32}", api_hash):
    raise SystemExit("TG_API_HASH secret is missing or is not a 32-character hexadecimal value.")

text = template.read_text(encoding="utf-8")
def set_property(source, key, value):
    pattern = re.compile(rf"(?m)^{re.escape(key)}=.*$")
    replacement = f"{key}={value}"
    updated, count = pattern.subn(lambda _: replacement, source)
    if count == 0:
        updated += f"\n{replacement}\n"
    elif count != 1:
        raise SystemExit(f"Expected one {key} property in template, found {count}.")
    return updated

text = set_property(text, "TELEGRAM_API_ID", api_id)
text = set_property(text, "TELEGRAM_API_HASH", api_hash)
destination.write_text(text, encoding="utf-8")
destination.chmod(0o600)
print("private.properties created; secret values were not printed.")

# backend.py

import os
import csv
import uuid
import requests
from requests.auth import HTTPBasicAuth

ACTION_MAP = {
    "0": "Ignore",
    "1": "Hang Up",
    "4": "Take Message",
    "5": "Skip Greeting",
    "6": "Restart Greeting",
    "7": "Transfer to alternate contact number",
    "8": "Route from next call routing rule"
}

def export_call_handlers_menu_entries_sse(base_url, username, password, output_csv):
    """
    This is a generator function that:
      1. Fetches /vmrest/handlers/callhandlers/?query=(IsPrimary%20is%200) to get the total and call handlers.
      2. Yields SSE 'progress' events after each call handler is processed.
      3. Yields a final 'done' event with the CSV filename.

    The Flask route will wrap this generator in a Response with mimetype='text/event-stream'.
    """

    session = requests.Session()
    session.auth = HTTPBasicAuth(username, password)
    session.verify = False
    session.headers.update({"Accept": "application/json"})

    handlers_url = f"{base_url}/vmrest/handlers/callhandlers/?query=(IsPrimary%20is%200)"
    resp = session.get(handlers_url)
    resp.raise_for_status()

    data = resp.json()

    # total string might be in data["@total"]
    total_str = data.get("@total", "0")
    try:
        total_count = int(total_str)
    except ValueError:
        total_count = 0

    call_handlers = data.get("Callhandler", [])
    if not isinstance(call_handlers, list):
        # Sometimes, if there's exactly one result, it might be a dict. Make it a list for consistency.
        call_handlers = [call_handlers]

    # Prepare to write CSV
    fieldnames = [
        "CallHandlerName",
        "MenuEntryObjectId",
        "TouchtoneKey",
        "ActionCode",
        "ActionDescription",
        "MenuEntryDisplayName",
        "TransferNumber",
        "TransferType",
        "TransferRings"
    ]
    with open(output_csv, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        processed_count = 0  # how many we've processed so far

        for handler in call_handlers:
            ch_display_name = handler.get("DisplayName", "(no name)")
            menu_entries_uri = handler.get("MenuEntriesURI")
            if not menu_entries_uri:
                processed_count += 1
                yield make_sse("progress", f"{processed_count},{total_count}")
                continue

            # Fetch this handler's menu entries
            full_menu_url = f"{base_url}{menu_entries_uri}"
            menu_resp = session.get(full_menu_url)
            menu_resp.raise_for_status()

            menu_data = menu_resp.json()
            menu_entries = menu_data.get("MenuEntry", [])
            if not isinstance(menu_entries, list):
                menu_entries = [menu_entries]

            # Write each entry to CSV
            for entry in menu_entries:
                action_code = str(entry.get("Action", ""))
                action_description = ACTION_MAP.get(action_code, f"Unknown ({action_code})")

                row = {
                    "CallHandlerName": ch_display_name,
                    "MenuEntryObjectId": entry.get("ObjectId", ""),
                    "TouchtoneKey": entry.get("TouchtoneKey", ""),
                    "ActionCode": action_code,
                    "ActionDescription": action_description,
                    "MenuEntryDisplayName": entry.get("DisplayName", ""),
                    "TransferNumber": entry.get("TransferNumber", ""),
                    "TransferType": entry.get("TransferType", ""),
                    "TransferRings": entry.get("TransferRings", "")
                }
                writer.writerow(row)

            # One handler done => update processed_count
            processed_count += 1
            # Send SSE "progress" event with "processed_count,total_count"
            yield make_sse("progress", f"{processed_count},{total_count}")

    # After we finish, yield an SSE event "done" with the filename
    yield make_sse("done", os.path.basename(output_csv))


def make_sse(event_type, data_str):
    """
    Utility to format a server-sent event message.
    SSE format is:
      event: <event_type>\n
      data: <data_str>\n
      \n
    """
    return f"event: {event_type}\ndata: {data_str}\n\n"

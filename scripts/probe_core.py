#!/usr/bin/env python3
"""Read earbud settings and print a diagnostic summary."""

import argparse
import json
import sys
import time
from pathlib import Path

component = Path(__file__).resolve().parents[1] / "custom_components" / "redmi_buds"
if not component.is_dir():
    component = Path("/config/custom_components/redmi_buds")
sys.path.insert(0, str(component))
from mma import BudsClient, BudsError  # noqa: E402
from mma.model import ACTIONS, EQ_PROFILES, label_for  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "address", help="Bluetooth MAC of already paired Redmi Buds 6 Play"
    )
    parser.add_argument("--channel", type=int, default=6, choices=range(1, 31))
    args = parser.parse_args()
    client = BudsClient(args.address, args.channel)
    started = time.monotonic()
    try:
        data = client.read()
        print(
            json.dumps(
                {
                    "result": "OK",
                    "seconds": round(time.monotonic() - started, 2),
                    "battery_percent": [b.level for b in data.info.batteries]
                    if data.info.batteries
                    else None,
                    "charging": [b.charging for b in data.info.batteries]
                    if data.info.batteries
                    else None,
                    "low_latency": data.latency,
                    "equalizer": label_for(EQ_PROFILES, data.equalizer),
                    "gestures_by_type": {
                        str(k): [label_for(ACTIONS, v) for v in values]
                        for k, values in data.gestures.items()
                    },
                    "firmware_raw": data.info.firmware_raw,
                    "firmware_version": data.info.firmware_version,
                    "model_id": data.info.model_id,
                    "timestamp": data.observed_at.isoformat(),
                },
                indent=2,
            )
        )
        return 0
    except BudsError as error:
        print(type(error).__name__ + ": " + str(error), file=sys.stderr)
        return 1
    finally:
        client.close()


if __name__ == "__main__":
    raise SystemExit(main())

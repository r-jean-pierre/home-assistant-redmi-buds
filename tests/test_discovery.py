"""BlueZ snapshots contain synthetic identities only."""

import unittest

from mma.bluez import parse_paired_devices


class DiscoveryTests(unittest.TestCase):
    def test_paired_public_devices_alias_and_deduplication(self):
        props = {
            "Paired": True,
            "Address": "aa:bb:cc:dd:ee:01",
            "AddressType": "public",
            "Name": "Redmi Buds 6 Play",
            "Alias": "My earbuds",
        }
        objects = {
            "/org/bluez/hci0": {"org.bluez.Adapter1": {}},
            "/org/bluez/hci0/dev_1": {"org.bluez.Device1": props},
            "/org/bluez/hci1/dev_1": {"org.bluez.Device1": props},
            "/org/bluez/hci0/dev_2": {
                "org.bluez.Device1": {
                    **props,
                    "Paired": False,
                    "Address": "AA:BB:CC:DD:EE:02",
                }
            },
            "/org/bluez/hci0/dev_3": {
                "org.bluez.Device1": {
                    **props,
                    "Blocked": True,
                    "Address": "AA:BB:CC:DD:EE:03",
                }
            },
            "/org/bluez/hci0/dev_4": {
                "org.bluez.Device1": {
                    **props,
                    "AddressType": "random",
                    "Address": "AA:BB:CC:DD:EE:04",
                }
            },
            "/org/bluez/hci0/dev_5": {
                "org.bluez.Device1": {**props, "Address": "invalid"}
            },
            "/org/bluez/hci0/dev_6": {
                "org.bluez.Device1": {
                    "Paired": True,
                    "Address": "AA:BB:CC:DD:EE:06",
                    "Alias": "Renamed headphones",
                }
            },
        }
        result = parse_paired_devices(objects)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].address, "AA:BB:CC:DD:EE:01")
        self.assertEqual(result[0].name, "My earbuds")
        self.assertTrue(result[0].likely_model)
        self.assertFalse(result[1].likely_model)

    def test_empty_and_malformed_objects(self):
        self.assertEqual(parse_paired_devices({}), [])
        self.assertEqual(
            parse_paired_devices({"a": None, "b": {"org.bluez.Device1": []}}), []
        )

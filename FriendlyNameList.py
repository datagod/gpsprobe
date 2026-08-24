# Known devices: MAC address -> friendly name
# GPSProbe imports this dict and copies it into the SQLite FriendlyName table.
# Keys should match packet MACs (typically lowercase hex with colons).
#
# This file was missing from the repo; add your own devices here.

FriendlyNameList = {
    # "aa:bb:cc:dd:ee:ff": "Living room AP",
    # "11:22:33:44:55:66": "Alice phone",
}

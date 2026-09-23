#!/bin/env python3

# This sample demonstrates how to snapshot a symbol.

from activfinancial import *
from activfinancial.constants import *

import common

# Create and connect the session (credentials and data source are set in common.py).
session = common.connect_session()

# Snapshot the VIX topic.
# Returns a SnapshotMessage
msg = session.snapshot("=VIX.WI")
print(f'SNAPSHOT received for {msg.symbol}')
print(common.snapshot_message_to_string(msg, session.metadata))

# Snapshot the VSTOXX topic.
# Returns a SnapshotMessage
msg = session.snapshot("=V2TX.XE")
print(f'SNAPSHOT received for {msg.symbol}')
print(common.snapshot_message_to_string(msg, session.metadata))

# Snapshot the MOVE topic.
# Returns a SnapshotMessage
msg = session.snapshot("=MOVE.NGI")
print(f'SNAPSHOT received for {msg.symbol}')
print(common.snapshot_message_to_string(msg, session.metadata))
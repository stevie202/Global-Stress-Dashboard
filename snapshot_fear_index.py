#!/bin/env python3

# This sample demonstrates how to snapshot a symbol.

from activfinancial import *
from activfinancial.constants import *

import common

# Create the session.
session = Session()

#connect_parameters = {}
#connect_parameters[FID_HOST]     = 'aop-replay.activfinancial.com'
#connect_parameters[FID_USER_ID]  = 'user id'
#connect_parameters[FID_PASSWORD] = 'password'

# Connect synchronously.
session.connect(connect_parameters)

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
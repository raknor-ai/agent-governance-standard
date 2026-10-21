"""Verify 38.ots without trusting the ledger operator or a local Bitcoin node.

Replays the proof's operations from the digest to each Bitcoin attestation, then compares the
resulting merkle root with block headers fetched from two independent public explorers.
"""
import json, sys, urllib.request
from opentimestamps.core.timestamp import DetachedTimestampFile
from opentimestamps.core.notary import BitcoinBlockHeaderAttestation
from opentimestamps.core.serialize import StreamDeserializationContext

EXPLORERS = ["https://mempool.space/api", "https://blockstream.info/api"]

def get(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read().decode()

def header(api, height):
    h = get(f"{api}/block-height/{height}").strip()
    b = json.loads(get(f"{api}/block/{h}"))
    return h, b["merkle_root"], b["timestamp"], b.get("mediantime")

ots_path, expected_digest = sys.argv[1], sys.argv[2]
with open(ots_path, "rb") as f:
    dtf = DetachedTimestampFile.deserialize(StreamDeserializationContext(f))

print("proof file digest :", dtf.file_digest.hex())
print("matches record    :", dtf.file_digest.hex() == expected_digest)

found = False
for msg, att in dtf.timestamp.all_attestations():
    if not isinstance(att, BitcoinBlockHeaderAttestation):
        print("other attestation :", att)
        continue
    found = True
    root = msg[::-1].hex()  # OTS commits the internal byte order; explorers display reversed
    print(f"bitcoin attestation: height {att.height}, proof merkle root {root}")
    for api in EXPLORERS:
        try:
            bh, mr, ts, mtp = header(api, att.height)
            print(f"  {api.split('/')[2]:<18} block {bh[:16]}… root match={mr == root} header_time={ts} mediantime={mtp}")
        except Exception as e:
            print(f"  {api.split('/')[2]:<18} ERROR {e}")
if not found:
    print("no Bitcoin attestation in proof (pending/calendar-only)")

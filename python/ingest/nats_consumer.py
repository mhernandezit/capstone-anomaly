import asyncio
import yaml
from nats.aio.client import Client as NATS
from python.utils.schema import BGPUpdate
from python.features.stream_features import FeatureAggregator
from python.models.mp_detector import MPDetector
from python.triage.impact import ImpactScorer

CFG_ROLES = yaml.safe_load(open("configs/roles.yml"))
BIN_SECS = CFG_ROLES["binning"]["bin_seconds"]


async def main():
    nc = NATS()
    await nc.connect(servers=["nats://127.0.0.1:4222"])

    agg = FeatureAggregator(bin_seconds=BIN_SECS)
    mp = MPDetector(window_bins=CFG_ROLES["binning"]["window_bins"])
    impact = ImpactScorer(CFG_ROLES)

    async def handler(msg):
        upd = BGPUpdate.model_validate_json(msg.data)
        agg.add_update(upd)
        # When a bin closes, compute features → MP → triage
        while agg.has_closed_bin():
            fb = agg.pop_closed_bin()
            score = mp.update(fb)  # anomaly score for this bin
            triage = impact.classify(fb, score)
            # TODO: publish to dashboard channel (NATS or websocket)
            print({"bin": fb.bin_end, "mp_score": score, "triage": triage})

    await nc.subscribe("bgp.updates", cb=handler)
    try:
        while True:
            await asyncio.sleep(0.5)
    finally:
        await nc.drain()


if __name__ == "__main__":
    asyncio.run(main())

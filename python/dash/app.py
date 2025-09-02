import streamlit as st
import asyncio
from nats.aio.client import Client as NATS
import json

st.set_page_config(page_title="BGP Failure Detector", layout="wide")
placeholder = st.empty()


async def main():
    nc = NATS()
    await nc.connect(servers=["nats://nats:4222"])
    msgs = []

    async def cb(msg):
        data = json.loads(msg.data)
        msgs.append(data)
        with placeholder.container():
            st.subheader("Latest Event")
            st.json(data)

    await nc.subscribe("bgp.events", cb=cb)  # TODO: publish events from pipeline
    while True:
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    asyncio.run(main())

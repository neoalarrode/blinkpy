"""Manual test script to exercise BlinkLiveStream against a real account.

Usage:
    CREDFILE=creds.json CAMERA_NAME="Front Door" python -m blinkapp.try_livestream

Then point a player at the printed tcp:// URL, e.g.:
    ffplay tcp://127.0.0.1:12345
"""

import asyncio
from os import environ
from aiohttp import ClientSession
from blinkpy.blinkpy import Blink
from blinkpy.auth import Auth, BlinkTwoFARequiredError
from blinkpy.helpers.util import json_load

CREDFILE = environ.get("CREDFILE")
CAMERA_NAME = environ.get("CAMERA_NAME")


async def main():
    """Authenticate, start a liveview, and proxy it on a local TCP port."""
    session = ClientSession()
    blink = Blink(session=session)
    blink.auth = Auth(await json_load(CREDFILE), session=session)
    try:
        await blink.start()
    except BlinkTwoFARequiredError:
        await blink.prompt_2fa()

    camera = blink.cameras.get(CAMERA_NAME)
    if camera is None:
        print(f"Camera '{CAMERA_NAME}' not found. Available: {list(blink.cameras)}")
        await session.close()
        return

    livestream = await camera.init_livestream()
    await livestream.start(host="127.0.0.1", port=0)
    print(f"Streaming '{CAMERA_NAME}' at {livestream.url}")
    print("Connect a player, e.g.: ffplay", livestream.url)

    try:
        await livestream.feed()
    finally:
        await blink.save(CREDFILE)
        await session.close()


if __name__ == "__main__":
    asyncio.run(main())

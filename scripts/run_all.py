import asyncio
import os

import uvicorn

from bot.main import main as run_bot


async def run_api() -> None:
    port = int(os.getenv("PORT", "8000"))
    config = uvicorn.Config("api.main:app", host="0.0.0.0", port=port, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


async def main() -> None:
    await asyncio.gather(run_api(), run_bot())


if __name__ == "__main__":
    asyncio.run(main())

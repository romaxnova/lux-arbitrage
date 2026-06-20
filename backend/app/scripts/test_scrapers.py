"""Integration test for live scrapers (no database)."""

import asyncio
import json

from app.scrapers.oskelly import OskellyAdapter
from app.scrapers.vinted import VintedAdapter


async def main():
    vinted = VintedAdapter()
    oskelly = OskellyAdapter()

    v = await vinted.fetch_listings("Prada", "bags", limit=5)
    o = await oskelly.fetch_listings("Prada", "bags", limit=5)

    print(f"Vinted: {len(v)} listings")
    for item in v[:2]:
        print(f"  {item.external_id} | {item.brand} | {item.title[:40]} | EUR {item.price}")

    print(f"Oskelly: {len(o)} listings")
    for item in o[:2]:
        print(f"  {item.external_id} | {item.brand} | {item.title[:40]} | RUB {item.price}")

    with open("scraper-test-output.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "vinted_count": len(v),
                "oskelly_count": len(o),
                "vinted_sample": [item.__dict__ for item in v[:3]],
                "oskelly_sample": [item.__dict__ for item in o[:3]],
            },
            f,
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    print("saved scraper-test-output.json")


if __name__ == "__main__":
    asyncio.run(main())

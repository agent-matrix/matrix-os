#!/usr/bin/env python3
"""Capture screenshots of the Matrix OS Admin Console for the README.

The console is a client-side SPA (React + Babel via CDN), so routes are reached
by clicking the sidebar rather than by URL. Run the server first:

    .venv/bin/python -m matrix_os serve --port 8099
    .venv/bin/python scripts/shoot.py --base-url http://127.0.0.1:8099
"""

import argparse
import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


async def settle(page, ms=1200):
    await page.wait_for_timeout(ms)


async def shoot(page, out: Path, name):
    await settle(page)
    p = out / f"{name}.png"
    await page.screenshot(path=str(p), full_page=False)
    print("shot:", p)


async def nav(page, label):
    """Click a sidebar nav item by its label."""
    await page.locator(".navitem", has_text=label).first.click()
    await settle(page, 900)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8099")
    ap.add_argument("--out", default="docs/screenshots")
    ap.add_argument("--width", type=int, default=1512)
    ap.add_argument("--height", type=int, default=945)
    ap.add_argument("--scale", type=int, default=2)
    args = ap.parse_args()

    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True, args=["--ignore-certificate-errors"]
        )
        ctx = await browser.new_context(
            viewport={"width": args.width, "height": args.height},
            device_scale_factor=args.scale,
            color_scheme="dark",
            ignore_https_errors=True,  # sandbox proxies HTTPS with an untrusted CA
        )
        page = await ctx.new_page()
        await page.goto(args.base_url, wait_until="networkidle")
        # Wait for the SPA (Babel transform + React render) to mount.
        await page.wait_for_selector(".brand", timeout=20000)
        await page.wait_for_selector(".metric", timeout=20000)
        await settle(page, 1800)  # let entrance animations + rain settle

        await shoot(page, out, "overview")

        await nav(page, "AI Coder")
        await page.wait_for_selector("text=GitPilot repair loop", timeout=8000)
        await shoot(page, out, "ai-coder")

        # Approval tab — the human-in-the-loop governance gate.
        try:
            await page.get_by_role("button", name="Approval").first.click(timeout=4000)
            await settle(page, 700)
            await shoot(page, out, "ai-coder-approval")
        except Exception as exc:
            print("skipped approval:", exc)

        await nav(page, "System")
        await shoot(page, out, "system")

        await browser.close()
    print("done")


if __name__ == "__main__":
    asyncio.run(main())

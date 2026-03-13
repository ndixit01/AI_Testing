#!/usr/bin/env python3
"""
Work Order Verification Automation
====================================
Iterates through the "Work Order Verifications" column on the dashboard
(https://repairs.signaltaxi.com/msys), top to bottom.

For each work order:
  1. Click the work order link
  2. Check the "Last Edit" date — stop if it is on or before STOP_DATE
  3. Click the "Verify" button
  4. Scroll to the bottom and click "Save"
  5. Navigate back to the dashboard and repeat

Usage:
  1. Install dependencies:  pip install playwright && playwright install chromium
  2. Run:                    python verify_work_orders.py
  3. Log in manually in the browser window that opens, then press Enter in the terminal.
"""

import asyncio
import re
from datetime import datetime

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# ── Configuration ──────────────────────────────────────────────────────────────
BASE_URL   = "https://repairs.signaltaxi.com/msys"
STOP_DATE  = datetime(2026, 3, 1)   # Stop when Last Edit <= this date
SLOW_MO_MS = 400                    # ms between actions (reduce if too slow)
# ───────────────────────────────────────────────────────────────────────────────


def parse_last_edit(text: str) -> datetime | None:
    """
    Parse dates like:
      "Tuesday, February 10, 2026, 4:44 PM"
      "Friday, February 27, 2026, 2:14 PM"
    Returns a datetime or None if parsing fails.
    """
    text = text.strip()
    # Remove the day-of-week prefix ("Tuesday, ")
    text = re.sub(r"^[A-Za-z]+,\s*", "", text)
    for fmt in ("%B %d, %Y, %I:%M %p", "%B %d, %Y, %I:%M%p",
                "%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


async def get_column_links(page) -> list[tuple[str, str]]:
    """
    Return all (text, href) pairs from the Work Order Verifications column,
    excluding navigation/utility links like '[ View All ]'.
    """
    # Find the column header, walk up to its card container, collect links.
    header = page.locator("text=Work Order Verifications")
    # The header is inside a card; collect all <a> tags in the same card.
    card = header.locator("xpath=ancestor::*[self::div or self::td or self::section][1]")
    anchors = card.locator("a")
    count = await anchors.count()

    results = []
    for i in range(count):
        a = anchors.nth(i)
        href = await a.get_attribute("href")
        text = (await a.inner_text()).strip()
        if href and text and "View All" not in text:
            results.append((text, href))
    return results


async def get_last_edit_date(page) -> datetime | None:
    """Read the Last Edit field from the Edit Work Order page."""
    try:
        # The label "Last Edit" is followed by the date text in an adjacent cell/div.
        label = page.locator("text=Last Edit")
        # Try a following-sibling td or div.
        for xpath in (
            "xpath=following-sibling::td[1]",
            "xpath=following-sibling::div[1]",
            "xpath=../following-sibling::*[1]",
        ):
            sibling = label.locator(xpath)
            if await sibling.count() > 0:
                raw = (await sibling.inner_text()).strip()
                if raw:
                    return parse_last_edit(raw)
    except Exception:
        pass
    return None


async def main() -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=SLOW_MO_MS)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(BASE_URL)

        print("=" * 60)
        print("Browser is open. Please log in to the application.")
        print("Once the Dashboard is fully visible, press Enter here.")
        print("=" * 60)
        input()

        processed: set[str] = set()
        total_verified = 0

        while True:
            await page.wait_for_load_state("networkidle")

            links = await get_column_links(page)
            pending = [(t, h) for t, h in links if h not in processed]

            if not pending:
                print(f"\nNo more pending work orders. Total verified: {total_verified}")
                break

            text, href = pending[0]   # top-to-bottom: take the first unprocessed
            print(f"\n[{total_verified + 1}] Opening: {text}")

            # ── Navigate to work order ──────────────────────────────────────
            await page.click(f'a[href="{href}"]')
            await page.wait_for_load_state("networkidle")

            # ── Stop-date check ─────────────────────────────────────────────
            wo_date = await get_last_edit_date(page)
            if wo_date:
                print(f"     Last Edit: {wo_date.strftime('%m/%d/%Y %I:%M %p')}")
                if wo_date <= STOP_DATE:
                    print(f"     STOP — date is on or before {STOP_DATE.strftime('%m/%d/%Y')}.")
                    print(f"     Total verified this session: {total_verified}")
                    await page.go_back()
                    break
            else:
                print("     WARNING: could not read Last Edit date — continuing anyway.")

            # ── Click Verify ────────────────────────────────────────────────
            verify = page.locator('button:has-text("Verify")')
            if await verify.count() == 0:
                print("     WARNING: Verify button not found — skipping.")
                processed.add(href)
                await page.go_back()
                await page.wait_for_load_state("networkidle")
                continue

            await verify.first.click()
            await page.wait_for_load_state("networkidle")
            print("     Clicked Verify")

            # ── Scroll to bottom, click Save ────────────────────────────────
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(600)

            # Prefer the plain "Save" button (not "Save & Close" or "Delete")
            save = page.locator('button:has-text("Save"):not(:has-text("Close")):not(:has-text("&"))')
            if await save.count() == 0:
                # Fallback: any Save button
                save = page.locator('button:has-text("Save")').first

            await save.first.click()
            await page.wait_for_load_state("networkidle")
            print("     Clicked Save")

            total_verified += 1
            processed.add(href)

            # ── Back to dashboard ───────────────────────────────────────────
            await page.go_back()
            await page.wait_for_load_state("networkidle")
            print(f"     Done. ({total_verified} verified so far)")

        print("\nScript finished.")
        input("Press Enter to close the browser...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

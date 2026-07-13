from __future__ import annotations

from pathlib import Path

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

BASE_URL = "http://localhost:8000"

OUTPUT_DIR = (
    PROJECT_ROOT
    / "docs"
    / "screenshots"
)


def capture(
    page: Page,
    name: str,
    url: str,
) -> None:
    destination = OUTPUT_DIR / f"{name}.png"

    print(
        f"Capturing {BASE_URL}{url}"
    )

    page.goto(
        f"{BASE_URL}{url}",
        wait_until="networkidle",
        timeout=60_000,
    )

    page.screenshot(
        path=str(destination),
        full_page=True,
    )

    print(
        f"Created {destination}"
    )


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pages = {
        "swagger-api": "/docs",
        "redoc-api": "/redoc",
    }

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=True,
        )

        page = browser.new_page(
            viewport={
                "width": 1600,
                "height": 1000,
            },
            device_scale_factor=1,
        )

        try:
            for name, url in pages.items():
                capture(
                    page=page,
                    name=name,
                    url=url,
                )

        except PlaywrightTimeoutError as error:
            raise RuntimeError(
                "NetPulse did not become ready for screenshots."
            ) from error

        finally:
            browser.close()


if __name__ == "__main__":
    main()
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

    print(f"Capturing {BASE_URL}{url}")

    response = page.goto(
        f"{BASE_URL}{url}",
        wait_until="domcontentloaded",
        timeout=60_000,
    )

    if response is None:
        raise RuntimeError(
            f"No HTTP response received for {url}"
        )

    if not response.ok:
        raise RuntimeError(
            f"Screenshot page returned HTTP "
            f"{response.status}: {url}"
        )

    if url == "/portfolio":
        page.wait_for_selector(
            'body[data-dashboard-ready="true"]',
            state="attached",
            timeout=30_000,
        )

        page.wait_for_timeout(1_000)
    else:
        page.wait_for_load_state(
            "networkidle",
            timeout=30_000,
        )

    page.screenshot(
        path=str(destination),
        full_page=True,
    )

    print(f"Created {destination}")


def main() -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pages = {
        "portfolio-dashboard": "/portfolio",
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

        page.on(
            "console",
            lambda message: print(
                f"[browser:{message.type}] "
                f"{message.text}"
            ),
        )

        page.on(
            "pageerror",
            lambda error: print(
                f"[browser-error] {error}"
            ),
        )

        try:
            for name, url in pages.items():
                capture(
                    page=page,
                    name=name,
                    url=url,
                )

        except PlaywrightTimeoutError as error:
            debug_path = (
                OUTPUT_DIR
                / "portfolio-timeout-debug.png"
            )

            page.screenshot(
                path=str(debug_path),
                full_page=True,
            )

            print(
                f"Debug screenshot created: "
                f"{debug_path}"
            )

            raise RuntimeError(
                "NetPulse did not become ready "
                "for screenshots."
            ) from error

        finally:
            browser.close()


if __name__ == "__main__":
    main()
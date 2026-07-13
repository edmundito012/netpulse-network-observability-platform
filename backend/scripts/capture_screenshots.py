from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:8000"

OUTPUT_DIR = Path("docs/screenshots")


def capture(page, name, url):

    page.goto(
        f"{BASE_URL}{url}",
        wait_until="networkidle",
    )

    page.screenshot(
        path=OUTPUT_DIR / f"{name}.png",
        full_page=True,
    )


def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
        )

        page = browser.new_page(
            viewport={
                "width": 1600,
                "height": 1000,
            }
        )

        capture(
            page,
            "swagger",
            "/docs",
        )

        capture(
            page,
            "redoc",
            "/redoc",
        )

        browser.close()


if __name__ == "__main__":
    main()
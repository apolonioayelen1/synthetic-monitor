import re

from playwright.sync_api import Page, expect


class BasePage:
    """Base Page Object providing shared navigation and web-first assertion helpers."""

    def __init__(self, page: Page, base_url: str) -> None:
        self.page = page
        self.base_url = base_url.rstrip("/")

    @property
    def current_url(self) -> str:
        return self.page.url

    def navigate(self, path: str = "/") -> None:
        target = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        self.page.goto(target, wait_until="domcontentloaded")

    def expect_url_contains(self, fragment: str) -> None:
        expect(self.page).to_have_url(re.compile(re.escape(fragment)))
from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage


class LoginPage(BasePage):
    """Page Object for the SauceDemo login screen."""

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.username_input = page.locator('[data-test="username"]')
        self.password_input = page.locator('[data-test="password"]')
        self.login_button = page.locator('[data-test="login-button"]')
        self.error_banner = page.locator('[data-test="error"]')

    def open(self) -> None:
        self.navigate("/")
        expect(self.login_button).to_be_visible()

    def login(self, username: str, password: str) -> None:
        assert username and password, (
            "MONITOR_USERNAME and MONITOR_PASSWORD must be configured in .env or CI Secrets."
        )
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
        self.expect_url_contains("/inventory.html")
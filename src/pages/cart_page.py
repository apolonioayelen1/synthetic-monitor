from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage


class CartPage(BasePage):
    """Page Object for the SauceDemo shopping cart screen."""

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.cart_item_name = page.locator('[data-test="inventory-item-name"]')
        self.checkout_button = page.locator('[data-test="checkout"]')

    def verify_item_present(self, expected_item: str = "Sauce Labs Backpack") -> None:
        expect(self.cart_item_name.first).to_contain_text(expected_item)

    def proceed_to_checkout(self) -> None:
        self.checkout_button.click()
        self.expect_url_contains("/checkout-step-one.html")
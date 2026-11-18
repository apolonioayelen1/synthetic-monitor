from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage


class InventoryPage(BasePage):
    """Page Object for the SauceDemo product inventory screen."""

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.inventory_list = page.locator('[data-test="inventory-list"]')
        self.add_backpack_button = page.locator('[data-test="add-to-cart-sauce-labs-backpack"]')
        self.cart_badge = page.locator('[data-test="shopping-cart-badge"]')
        self.cart_link = page.locator('[data-test="shopping-cart-link"]')

    def verify_loaded(self) -> None:
        expect(self.inventory_list).to_be_visible()

    def add_backpack_to_cart(self) -> None:
        self.add_backpack_button.click()
        expect(self.cart_badge).to_have_text("1")

    def go_to_cart(self) -> None:
        self.cart_link.click()
        self.expect_url_contains("/cart.html")
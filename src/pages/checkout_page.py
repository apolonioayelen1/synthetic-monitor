from playwright.sync_api import Page, expect

from src.pages.base_page import BasePage


class CheckoutPage(BasePage):
    """Page Object for the SauceDemo checkout steps and order confirmation."""

    def __init__(self, page: Page, base_url: str) -> None:
        super().__init__(page, base_url)
        self.first_name_input = page.locator('[data-test="firstName"]')
        self.last_name_input = page.locator('[data-test="lastName"]')
        self.postal_code_input = page.locator('[data-test="postalCode"]')
        self.continue_button = page.locator('[data-test="continue"]')
        self.total_label = page.locator('[data-test="total-label"]')
        self.finish_button = page.locator('[data-test="finish"]')
        self.complete_header = page.locator('[data-test="complete-header"]')

    def fill_customer_info(
        self,
        first_name: str = "Synthetic",
        last_name: str = "Monitor",
        postal_code: str = "1000",
    ) -> None:
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.postal_code_input.fill(postal_code)
        self.continue_button.click()
        self.expect_url_contains("/checkout-step-two.html")

    def complete_order(self) -> None:
        expect(self.total_label).to_be_visible()
        self.finish_button.click()
        self.expect_url_contains("/checkout-complete.html")
        expect(self.complete_header).to_have_text("Thank you for your order!")
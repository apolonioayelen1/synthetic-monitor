import logging

import pytest
from playwright.sync_api import Playwright

from src.core.api_health import check_api_health
from src.core.config import Settings
from src.core.sla_timer import measure_step
from src.observability.metrics import MetricsCollector
from src.pages.cart_page import CartPage
from src.pages.checkout_page import CheckoutPage
from src.pages.inventory_page import InventoryPage
from src.pages.login_page import LoginPage
from tests.conftest import BrowserSessionManager


@pytest.mark.synthetic
def test_hybrid_ecommerce_synthetic_journey(
    settings: Settings,
    logger: logging.Logger,
    metrics_collector: MetricsCollector,
    pw_instance: Playwright,
    browser_session: BrowserSessionManager,
) -> None:
    """Execute API pre-flight check followed by critical UI e-commerce journey under SLA."""
    sla = settings.sla_threshold_seconds

    # 1. Backend / API Availability Check (before browser cold-start)
    check_api_health(
        playwright=pw_instance,
        url=settings.api_health_url,
        sla_threshold_seconds=sla,
        collector=metrics_collector,
        logger=logger,
    )

    # 2. Launch Browser (cold-start excluded from pure UI step timings)
    page = browser_session.start()

    login_page = LoginPage(page, settings.base_url)
    inventory_page = InventoryPage(page, settings.base_url)
    cart_page = CartPage(page, settings.base_url)
    checkout_page = CheckoutPage(page, settings.base_url)

    # 3. Critical UI Journey Steps
    with measure_step(
        name="ui_open_login",
        layer="UI",
        sla_threshold_seconds=sla,
        collector=metrics_collector,
        logger=logger,
        url_provider=lambda: login_page.current_url,
    ):
        login_page.open()

    with measure_step(
        name="ui_login_and_inventory",
        layer="UI",
        sla_threshold_seconds=sla,
        collector=metrics_collector,
        logger=logger,
        url_provider=lambda: login_page.current_url,
    ):
        login_page.login(settings.monitor_username, settings.monitor_password)
        inventory_page.verify_loaded()

    with measure_step(
        name="ui_add_to_cart_and_verify",
        layer="UI",
        sla_threshold_seconds=sla,
        collector=metrics_collector,
        logger=logger,
        url_provider=lambda: inventory_page.current_url,
    ):
        inventory_page.add_backpack_to_cart()
        inventory_page.go_to_cart()
        cart_page.verify_item_present("Sauce Labs Backpack")

    with measure_step(
        name="ui_checkout_completion",
        layer="UI",
        sla_threshold_seconds=sla,
        collector=metrics_collector,
        logger=logger,
        url_provider=lambda: checkout_page.current_url,
    ):
        cart_page.proceed_to_checkout()
        checkout_page.fill_customer_info()
        checkout_page.complete_order()

    logger.info("Synthetic Run Summary:\n" + metrics_collector.format_summary())
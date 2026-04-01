#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""End-to-end tests using live WooCommerce endpoint.

Run with: python -m pytest tests/test_e2e.py -v

WARNING: These tests use the live WooCommerce API!
They will create real orders and customers.
"""
import logging
import os
import time
from urllib.parse import urljoin, urlparse

import pytest
from dotenv import load_dotenv

# Load environment variables from tests/.env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from mcp_woocommerce_operator import MCPWooCommerceOperator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_woocommerce_settings():
    """Get WooCommerce settings from environment."""
    url = os.getenv("WOOCOMMERCE_URL", "")
    
    # Parse URL to extract base URL if it includes /wp-json/wc/v3
    if "/wp-json/" in url:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    else:
        base_url = url
    
    return {
        "woocommerce_url": base_url,
        "consumer_key": os.getenv("WOOCOMMERCE_CONSUMER_KEY"),
        "consumer_secret": os.getenv("WOOCOMMERCE_CONSUMER_SECRET"),
        "api_version": os.getenv("WOOCOMMERCE_API_VERSION", "wc/v3"),
        "verify_ssl": os.getenv("WOOCOMMERCE_VERIFY_SSL", "true").lower() == "true",
        "timeout": int(os.getenv("WOOCOMMERCE_TIMEOUT", "30")),
        "query_string_auth": os.getenv("WOOCOMMERCE_QUERY_STRING_AUTH", "false").lower() == "true",
    }


@pytest.fixture(scope="module")
def operator():
    """Create MCPWooCommerceOperator with live credentials."""
    settings = get_woocommerce_settings()
    
    # Validate required settings
    if not settings["consumer_key"] or not settings["consumer_secret"]:
        pytest.skip("WooCommerce credentials not configured")
    
    return MCPWooCommerceOperator(logger=logger, **settings)


@pytest.fixture
def test_timestamp():
    """Generate unique timestamp for test data."""
    return int(time.time())


class TestE2EProducts:
    """End-to-end tests for product operations."""

    def test_list_products(self, operator):
        """E2E: List products from live store."""
        result = operator.list_products(per_page=5)
        
        assert "products" in result
        assert isinstance(result["products"], list)
        logger.info(f"Found {len(result['products'])} products")
        
        if result["products"]:
            product = result["products"][0]
            assert "id" in product
            assert "name" in product
            logger.info(f"First product: {product.get('name')} (ID: {product.get('id')})")

    def test_list_products_with_search(self, operator):
        """E2E: Search products."""
        # First get all products to find a search term
        all_products = operator.list_products(per_page=10)
        
        if not all_products["products"]:
            pytest.skip("No products available to test search")
        
        # Use the first product name as search term
        search_term = all_products["products"][0]["name"].split()[0]  # First word
        result = operator.list_products(search=search_term, per_page=5)
        
        assert "products" in result
        logger.info(f"Search for '{search_term}' returned {len(result['products'])} products")

    def test_get_product_by_id(self, operator):
        """E2E: Get product by ID."""
        # First list products to get a valid ID
        products_result = operator.list_products(per_page=1)
        
        if not products_result["products"]:
            pytest.skip("No products available to test get_product")
        
        product_id = products_result["products"][0]["id"]
        result = operator.get_product(product_id=product_id)
        
        assert result["id"] == product_id
        assert "name" in result
        assert "price" in result
        logger.info(f"Retrieved product: {result.get('name')} - ${result.get('price')}")


class TestE2ECustomers:
    """End-to-end tests for customer operations."""

    def test_create_and_get_customer(self, operator, test_timestamp):
        """E2E: Create a customer and retrieve it."""
        # Create unique email
        email = f"test_customer_{test_timestamp}@example.com"
        
        # Create customer
        create_result = operator.create_customer(
            email=email,
            first_name="Test",
            last_name="Customer",
            billing={
                "first_name": "Test",
                "last_name": "Customer",
                "address_1": "123 Test St",
                "city": "Test City",
                "state": "CA",
                "postcode": "12345",
                "country": "US",
                "email": email,
                "phone": "555-123-4567",
            }
        )
        
        assert create_result["email"] == email
        assert create_result["first_name"] == "Test"
        customer_id = create_result["id"]
        logger.info(f"Created customer: {email} (ID: {customer_id})")
        
        # Retrieve by ID
        get_by_id = operator.get_customer(customer_id=customer_id)
        assert get_by_id["id"] == customer_id
        assert get_by_id["email"] == email
        
        # Retrieve by email
        get_by_email = operator.get_customer(email=email)
        assert get_by_email["id"] == customer_id
        assert get_by_email["email"] == email
        
        logger.info(f"Successfully retrieved customer by ID and email")


class TestE2EOrders:
    """End-to-end tests for order operations."""

    def test_list_orders(self, operator):
        """E2E: List orders from live store."""
        result = operator.list_orders(per_page=5)
        
        assert "orders" in result
        assert isinstance(result["orders"], list)
        logger.info(f"Found {len(result['orders'])} orders")
        
        if result["orders"]:
            order = result["orders"][0]
            assert "id" in order
            assert "status" in order
            logger.info(f"First order: ID {order.get('id')} - Status: {order.get('status')}")

    def test_list_orders_with_status_filter(self, operator):
        """E2E: List orders with status filter."""
        result = operator.list_orders(status="processing", per_page=5)
        
        assert "orders" in result
        
        # Verify all returned orders have the requested status
        for order in result["orders"]:
            assert order["status"] == "processing"
        
        logger.info(f"Found {len(result['orders'])} processing orders")

    def test_get_order(self, operator):
        """E2E: Get order details."""
        # First list orders to get a valid ID
        orders_result = operator.list_orders(per_page=1)
        
        if not orders_result["orders"]:
            pytest.skip("No orders available to test get_order")
        
        order_id = orders_result["orders"][0]["id"]
        result = operator.get_order(order_id=order_id)
        
        assert result["id"] == order_id
        assert "status" in result
        assert "total" in result
        assert "line_items" in result
        logger.info(f"Retrieved order: ID {order_id} - Total: ${result.get('total')}")

    def test_create_order(self, operator, test_timestamp):
        """E2E: Create an order."""
        # First get a product to order
        products = operator.list_products(per_page=1)
        if not products["products"]:
            pytest.skip("No products available to create order")
        
        product = products["products"][0]
        product_id = product["id"]
        
        # Create customer for the order
        email = f"order_test_{test_timestamp}@example.com"
        customer = operator.create_customer(
            email=email,
            first_name="Order",
            last_name="Test",
        )
        
        # Create order
        order_result = operator.create_order(
            customer_id=customer["id"],
            customer_email=email,
            customer_first_name="Order",
            customer_last_name="Test",
            billing_address={
                "first_name": "Order",
                "last_name": "Test",
                "address_1": "456 Order St",
                "city": "Order City",
                "state": "CA",
                "postcode": "67890",
                "country": "US",
                "email": email,
                "phone": "555-987-6543",
            },
            line_items=[
                {
                    "product_id": product_id,
                    "quantity": 1,
                }
            ],
            shipping_lines=[
                {
                    "method_id": "flat_rate",
                    "method_title": "Flat Rate",
                    "total": "10.00",
                }
            ],
            customer_note=f"Test order created at {test_timestamp}",
        )
        
        assert "id" in order_result
        assert order_result["status"] in ["pending", "processing"]
        order_id = order_result["id"]
        logger.info(f"Created order: ID {order_id} - Total: ${order_result.get('total')}")
        
        # Store order_id for cleanup or other tests
        return order_id

    def test_create_order_with_new_customer(self, operator, test_timestamp):
        """E2E: Create order with new customer email."""
        # Get a product
        products = operator.list_products(per_page=1)
        if not products["products"]:
            pytest.skip("No products available to create order")
        
        product = products["products"][0]
        
        # Create order with new customer
        email = f"new_customer_{test_timestamp}@example.com"
        order_result = operator.create_order(
            customer_email=email,
            customer_first_name="New",
            customer_last_name="Customer",
            billing_address={
                "first_name": "New",
                "last_name": "Customer",
                "address_1": "789 New St",
                "city": "New City",
                "state": "NY",
                "postcode": "11111",
                "country": "US",
                "email": email,
                "phone": "555-111-2222",
            },
            line_items=[
                {
                    "product_id": product["id"],
                    "quantity": 2,
                }
            ],
        )
        
        assert "id" in order_result
        logger.info(f"Created order for new customer: ID {order_result['id']}")

    def test_update_order_status(self, operator, test_timestamp):
        """E2E: Create order and update its status."""
        # Get a product
        products = operator.list_products(per_page=1)
        if not products["products"]:
            pytest.skip("No products available")
        
        # Create a simple order
        email = f"status_test_{test_timestamp}@example.com"
        order = operator.create_order(
            customer_email=email,
            customer_first_name="Status",
            customer_last_name="Test",
            billing_address={
                "first_name": "Status",
                "last_name": "Test",
                "address_1": "999 Status St",
                "city": "Status City",
                "state": "TX",
                "postcode": "77777",
                "country": "US",
                "email": email,
            },
            line_items=[{"product_id": products["products"][0]["id"], "quantity": 1}],
        )
        
        order_id = order["id"]
        logger.info(f"Created order for status update: ID {order_id}")
        
        # Update to processing
        updated = operator.update_order_status(
            order_id=order_id,
            status="processing",
            note="Order is now being processed",
        )
        assert updated["status"] == "processing"
        logger.info(f"Updated order to processing: ID {order_id}")
        
        # Update to completed
        completed = operator.update_order_status(
            order_id=order_id,
            status="completed",
            note="Order completed via E2E test",
        )
        assert completed["status"] == "completed"
        logger.info(f"Updated order to completed: ID {order_id}")


class TestE2EIntegration:
    """Integration tests combining multiple operations."""

    def test_full_order_workflow(self, operator, test_timestamp):
        """E2E: Complete order workflow from search to completion."""
        logger.info("Starting full order workflow test...")
        
        # Step 1: Search for a product
        products = operator.list_products(search="shirt", per_page=5)
        if not products["products"]:
            # Try any product
            products = operator.list_products(per_page=1)
        
        if not products["products"]:
            pytest.skip("No products available for integration test")
        
        product = products["products"][0]
        logger.info(f"Selected product: {product['name']} (ID: {product['id']})")
        
        # Step 2: Get detailed product info
        product_details = operator.get_product(product_id=product["id"])
        assert product_details["id"] == product["id"]
        logger.info(f"Product price: ${product_details.get('price')}")
        
        # Step 3: Create customer
        email = f"workflow_{test_timestamp}@example.com"
        customer = operator.create_customer(
            email=email,
            first_name="Workflow",
            last_name="Test",
            billing={
                "first_name": "Workflow",
                "last_name": "Test",
                "address_1": "123 Workflow Ave",
                "city": "Workflow City",
                "state": "FL",
                "postcode": "33333",
                "country": "US",
                "email": email,
                "phone": "555-333-4444",
            }
        )
        customer_id = customer["id"]
        logger.info(f"Created customer: {email} (ID: {customer_id})")
        
        # Step 4: Create order
        order = operator.create_order(
            customer_id=customer_id,
            customer_email=email,
            customer_first_name="Workflow",
            customer_last_name="Test",
            billing_address=customer["billing"],
            line_items=[{
                "product_id": product["id"],
                "quantity": 2,
            }],
            shipping_lines=[{
                "method_id": "flat_rate",
                "method_title": "Standard Shipping",
                "total": "15.00",
            }],
            customer_note="This is an integration test order",
        )
        order_id = order["id"]
        logger.info(f"Created order: ID {order_id}")
        
        # Step 5: Get order details
        order_details = operator.get_order(order_id=order_id)
        assert order_details["id"] == order_id
        assert len(order_details["line_items"]) == 1
        logger.info(f"Order total: ${order_details['total']}")
        
        # Step 6: Update order status
        updated = operator.update_order_status(
            order_id=order_id,
            status="processing",
            note="Order moved to processing",
        )
        assert updated["status"] == "processing"
        logger.info(f"Order status updated to processing")
        
        # Step 7: List orders to verify
        orders_list = operator.list_orders(customer_id=customer_id)
        assert any(o["id"] == order_id for o in orders_list["orders"])
        logger.info(f"Verified order appears in customer order list")
        
        logger.info("Full order workflow test completed successfully!")


def test_connection_and_authentication():
    """Test basic connectivity and authentication."""
    settings = get_woocommerce_settings()
    
    if not settings["consumer_key"] or not settings["consumer_secret"]:
        pytest.skip("WooCommerce credentials not configured")
    
    operator = MCPWooCommerceOperator(logger=logger, **settings)
    
    # Simple connectivity test - list products
    try:
        result = operator.list_products(per_page=1)
        logger.info(f"✓ Successfully connected to WooCommerce API")
        logger.info(f"✓ Found {len(result['products'])} products (requested 1)")
    except Exception as e:
        logger.error(f"✗ Failed to connect: {e}")
        raise


if __name__ == "__main__":
    # Run tests manually
    pytest.main([__file__, "-v", "--tb=short"])

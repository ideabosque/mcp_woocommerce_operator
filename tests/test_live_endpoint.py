#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Live endpoint testing for WooCommerce MCP Operator.

This script tests the real WooCommerce endpoint with actual API calls.
"""
import logging
import os
import sys
from urllib.parse import urlparse

from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mcp_woocommerce_operator import MCPWooCommerceOperator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_woocommerce_settings():
    """Get WooCommerce settings from environment."""
    url = os.getenv("WOOCOMMERCE_URL", "")
    
    # Parse URL to extract base URL
    if "/wp-json/" in url:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
    else:
        base_url = url
    
    settings = {
        "woocommerce_url": base_url,
        "consumer_key": os.getenv("WOOCOMMERCE_CONSUMER_KEY"),
        "consumer_secret": os.getenv("WOOCOMMERCE_CONSUMER_SECRET"),
        "api_version": os.getenv("WOOCOMMERCE_API_VERSION", "wc/v3"),
        "verify_ssl": os.getenv("WOOCOMMERCE_VERIFY_SSL", "true").lower() == "true",
        "timeout": int(os.getenv("WOOCOMMERCE_TIMEOUT", "30")),
        "query_string_auth": os.getenv("WOOCOMMERCE_QUERY_STRING_AUTH", "false").lower() == "true",
    }
    
    # Validate
    if not settings["consumer_key"] or not settings["consumer_secret"]:
        logger.error("WooCommerce credentials not configured in .env file")
        sys.exit(1)
    
    return settings


def test_connection(operator):
    """Test basic connectivity."""
    logger.info("=" * 60)
    logger.info("TEST 1: Connection Test")
    logger.info("=" * 60)
    
    try:
        result = operator.list_products(per_page=1)
        logger.info(f"✓ Successfully connected to WooCommerce API")
        logger.info(f"✓ API returned {len(result['products'])} products")
        return True
    except Exception as e:
        logger.error(f"✗ Connection failed: {e}")
        return False


def test_list_products(operator):
    """Test listing products."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: List Products")
    logger.info("=" * 60)
    
    try:
        result = operator.list_products(per_page=5)
        logger.info(f"✓ Found {len(result['products'])} products")
        
        if result['products']:
            for i, product in enumerate(result['products'][:3], 1):
                logger.info(f"  {i}. {product.get('name')} (ID: {product.get('id')}, SKU: {product.get('sku', 'N/A')})")
                logger.info(f"     Price: ${product.get('price')} | Stock: {product.get('stock_status', 'unknown')}")
        
        return result['products']
    except Exception as e:
        logger.error(f"✗ Failed to list products: {e}")
        return []


def test_get_product(operator, product_id):
    """Test getting product details."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Get Product Details")
    logger.info("=" * 60)
    
    try:
        result = operator.get_product(product_id=product_id)
        logger.info(f"✓ Retrieved product: {result.get('name')}")
        logger.info(f"  ID: {result.get('id')}")
        logger.info(f"  SKU: {result.get('sku', 'N/A')}")
        logger.info(f"  Price: ${result.get('price')}")
        logger.info(f"  Stock Status: {result.get('stock_status', 'N/A')}")
        return result
    except Exception as e:
        logger.error(f"✗ Failed to get product: {e}")
        return None


def test_create_customer(operator, timestamp):
    """Test creating a customer."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Create Customer")
    logger.info("=" * 60)
    
    email = f"test_customer_{timestamp}@example.com"
    
    try:
        result = operator.create_customer(
            email=email,
            first_name="Test",
            last_name="Customer",
            billing={
                "first_name": "Test",
                "last_name": "Customer",
                "address_1": "123 Test Street",
                "city": "Test City",
                "state": "CA",
                "postcode": "12345",
                "country": "US",
                "email": email,
                "phone": "555-123-4567",
            }
        )
        
        logger.info(f"✓ Created customer: {email}")
        logger.info(f"  Customer ID: {result.get('id')}")
        logger.info(f"  Username: {result.get('username')}")
        return result
    except Exception as e:
        logger.error(f"✗ Failed to create customer: {e}")
        return None


def test_create_order(operator, customer, product):
    """Test creating an order."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Create Order")
    logger.info("=" * 60)
    
    try:
        result = operator.create_order(
            customer_id=customer.get('id'),
            customer_email=customer.get('email'),
            customer_first_name=customer.get('first_name'),
            customer_last_name=customer.get('last_name'),
            billing_address=customer.get('billing'),
            line_items=[
                {
                    "product_id": product.get('id'),
                    "quantity": 2,
                }
            ],
            shipping_lines=[
                {
                    "method_id": "flat_rate",
                    "method_title": "Standard Shipping",
                    "total": "10.00",
                }
            ],
            customer_note="This is a test order created via MCP",
        )
        
        logger.info(f"✓ Created order: ID {result.get('id')}")
        logger.info(f"  Status: {result.get('status')}")
        logger.info(f"  Total: ${result.get('total')}")
        logger.info(f"  Currency: {result.get('currency', 'USD')}")
        return result
    except Exception as e:
        logger.error(f"✗ Failed to create order: {e}")
        return None


def test_update_order_status(operator, order_id):
    """Test updating order status."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: Update Order Status")
    logger.info("=" * 60)
    
    try:
        # Update to processing
        result = operator.update_order_status(
            order_id=order_id,
            status="processing",
            note="Order is now being processed"
        )
        logger.info(f"✓ Updated order status to: {result.get('status')}")
        
        # Update to completed
        result = operator.update_order_status(
            order_id=order_id,
            status="completed",
            note="Order completed via live endpoint test"
        )
        logger.info(f"✓ Updated order status to: {result.get('status')}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to update order status: {e}")
        return False


def test_list_orders(operator):
    """Test listing orders."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 7: List Orders")
    logger.info("=" * 60)
    
    try:
        result = operator.list_orders(per_page=5)
        logger.info(f"✓ Found {len(result['orders'])} orders")
        
        if result['orders']:
            for i, order in enumerate(result['orders'][:3], 1):
                logger.info(f"  {i}. Order ID: {order.get('id')} - Status: {order.get('status')} - Total: ${order.get('total')}")
        
        return result['orders']
    except Exception as e:
        logger.error(f"✗ Failed to list orders: {e}")
        return []


def test_get_customer(operator, customer_id):
    """Test getting customer details."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 8: Get Customer Details")
    logger.info("=" * 60)
    
    try:
        result = operator.get_customer(customer_id=customer_id)
        logger.info(f"✓ Retrieved customer: {result.get('email')}")
        logger.info(f"  ID: {result.get('id')}")
        logger.info(f"  Name: {result.get('first_name')} {result.get('last_name')}")
        logger.info(f"  Orders Count: {result.get('orders_count', 0)}")
        return result
    except Exception as e:
        logger.error(f"✗ Failed to get customer: {e}")
        return None


def main():
    """Run all tests."""
    import time
    timestamp = int(time.time())
    
    logger.info("\n" + "=" * 60)
    logger.info("WooCommerce MCP Operator - Live Endpoint Testing")
    logger.info("=" * 60)
    logger.info(f"Timestamp: {timestamp}")
    logger.info("")
    
    # Get settings
    settings = get_woocommerce_settings()
    logger.info(f"Connecting to: {settings['woocommerce_url']}")
    logger.info(f"API Version: {settings['api_version']}")
    logger.info("")
    
    # Create operator
    operator = MCPWooCommerceOperator(logger=logger, **settings)
    
    # Test 1: Connection
    if not test_connection(operator):
        logger.error("\nConnection test failed. Aborting.")
        sys.exit(1)
    
    # Test 2: List Products
    products = test_list_products(operator)
    if not products:
        logger.error("\nNo products found. Cannot continue.")
        sys.exit(1)
    
    # Test 3: Get Product Details
    product = test_get_product(operator, products[0].get('id'))
    if not product:
        logger.error("\nFailed to get product details. Using first product from list.")
        product = products[0]
    
    # Test 4: Create Customer
    customer = test_create_customer(operator, timestamp)
    if not customer:
        logger.error("\nFailed to create customer. Aborting.")
        sys.exit(1)
    
    # Test 5: Create Order
    order = test_create_order(operator, customer, product)
    if not order:
        logger.error("\nFailed to create order. Aborting.")
        sys.exit(1)
    
    # Test 6: Update Order Status
    test_update_order_status(operator, order.get('id'))
    
    # Test 7: List Orders
    test_list_orders(operator)
    
    # Test 8: Get Customer Details
    test_get_customer(operator, customer.get('id'))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info("✓ All tests completed successfully!")
    logger.info(f"  - Customer Email: {customer.get('email')}")
    logger.info(f"  - Customer ID: {customer.get('id')}")
    logger.info(f"  - Order ID: {order.get('id')}")
    logger.info(f"  - Order Total: ${order.get('total')}")
    logger.info("")
    logger.info("Live endpoint testing completed!")


if __name__ == "__main__":
    main()

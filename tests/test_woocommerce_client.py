#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for WooCommerceClient."""
import logging
from unittest.mock import MagicMock, patch

import pytest
import respx
from httpx import Response

from mcp_woocommerce_operator.woocommerce_client import WooCommerceClient


@pytest.fixture
def logger():
    """Create test logger."""
    return logging.getLogger("test")


@pytest.fixture
def client(logger):
    """Create WooCommerceClient instance for testing."""
    return WooCommerceClient(
        logger=logger,
        woocommerce_url="https://test-store.com",
        consumer_key="ck_test_key",
        consumer_secret="cs_test_secret",
    )


class TestWooCommerceClientInit:
    """Test client initialization."""

    def test_init_with_default_values(self, logger):
        """Test client initialization with default values."""
        client = WooCommerceClient(
            logger=logger,
            woocommerce_url="https://test-store.com",
            consumer_key="ck_test_key",
            consumer_secret="cs_test_secret",
        )

        assert client.woocommerce_url == "https://test-store.com"
        assert client.consumer_key == "ck_test_key"
        assert client.consumer_secret == "cs_test_secret"
        assert client.api_version == "wc/v3"
        assert client.verify_ssl is True
        assert client.timeout == 30
        assert client.query_string_auth is False
        assert client.base_url == "https://test-store.com/wp-json/wc/v3"

    def test_init_with_custom_values(self, logger):
        """Test client initialization with custom values."""
        client = WooCommerceClient(
            logger=logger,
            woocommerce_url="https://test-store.com/",
            consumer_key="ck_test_key",
            consumer_secret="cs_test_secret",
            api_version="wc/v2",
            verify_ssl=False,
            timeout=60,
            query_string_auth=True,
        )

        assert client.woocommerce_url == "https://test-store.com"
        assert client.api_version == "wc/v2"
        assert client.verify_ssl is False
        assert client.timeout == 60
        assert client.query_string_auth is True


class TestAuthentication:
    """Test authentication methods."""

    def test_basic_auth_headers(self, logger):
        """Test Basic Auth headers generation."""
        client = WooCommerceClient(
            logger=logger,
            woocommerce_url="https://test-store.com",
            consumer_key="ck_test_key",
            consumer_secret="cs_test_secret",
            query_string_auth=False,
        )

        headers = client._get_auth_headers()
        import base64

        expected_credentials = base64.b64encode(b"ck_test_key:cs_test_secret").decode()
        assert headers == {"Authorization": f"Basic {expected_credentials}"}

    def test_query_string_auth_params(self, logger):
        """Test query string auth parameters."""
        client = WooCommerceClient(
            logger=logger,
            woocommerce_url="https://test-store.com",
            consumer_key="ck_test_key",
            consumer_secret="cs_test_secret",
            query_string_auth=True,
        )

        params = client._get_query_params()
        assert params == {
            "consumer_key": "ck_test_key",
            "consumer_secret": "cs_test_secret",
        }


class TestOrders:
    """Test order operations."""

    @respx.mock
    def test_list_orders_success(self, client):
        """Test listing orders successfully."""
        # Mock response
        mock_orders = [
            {
                "id": 1,
                "status": "processing",
                "total": "99.99",
                "customer_id": 45,
            }
        ]
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(return_value=Response(200, json=mock_orders))

        result = client.list_orders(status="processing", per_page=10)

        assert result["orders"] == mock_orders
        assert result["page"] == 1
        assert result["per_page"] == 10
        assert route.called

    @respx.mock
    def test_list_orders_with_filters(self, client):
        """Test listing orders with filters."""
        mock_orders = []
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(return_value=Response(200, json=mock_orders))

        client.list_orders(
            status="completed",
            customer_id=123,
            date_from="2024-01-01T00:00:00Z",
            date_to="2024-12-31T23:59:59Z",
            page=2,
            per_page=50,
        )

        assert route.called
        request = route.calls[0].request
        assert b"status=completed" in request.url.query
        assert b"customer=123" in request.url.query
        assert b"after=2024-01-01T00%3A00%3A00Z" in request.url.query
        assert b"before=2024-12-31T23%3A59%3A59Z" in request.url.query
        assert b"page=2" in request.url.query
        assert b"per_page=50" in request.url.query

    @respx.mock
    def test_get_order_success(self, client):
        """Test getting a specific order."""
        mock_order = {
            "id": 123,
            "status": "completed",
            "total": "149.99",
            "line_items": [],
        }
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/orders/123"
        ).mock(return_value=Response(200, json=mock_order))

        result = client.get_order(123)

        assert result == mock_order
        assert route.called

    @respx.mock
    def test_create_order_success(self, client):
        """Test creating an order."""
        mock_order = {
            "id": 456,
            "status": "pending",
            "total": "99.99",
        }
        route = respx.post(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(return_value=Response(201, json=mock_order))

        order_data = {
            "billing": {"email": "test@example.com"},
            "line_items": [{"product_id": 1, "quantity": 2}],
        }
        result = client.create_order(order_data)

        assert result == mock_order
        assert route.called

    @respx.mock
    def test_update_order_success(self, client):
        """Test updating an order."""
        mock_order = {
            "id": 123,
            "status": "completed",
        }
        route = respx.put(
            "https://test-store.com/wp-json/wc/v3/orders/123"
        ).mock(return_value=Response(200, json=mock_order))

        result = client.update_order(123, {"status": "completed"})

        assert result == mock_order
        assert route.called


class TestProducts:
    """Test product operations."""

    @respx.mock
    def test_list_products_success(self, client):
        """Test listing products successfully."""
        mock_products = [
            {
                "id": 1,
                "name": "Test Product",
                "sku": "TEST-001",
                "price": "49.99",
            }
        ]
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/products"
        ).mock(return_value=Response(200, json=mock_products))

        result = client.list_products(search="test", per_page=10)

        assert result["products"] == mock_products
        assert result["page"] == 1
        assert route.called

    @respx.mock
    def test_list_products_with_filters(self, client):
        """Test listing products with filters."""
        mock_products = []
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/products"
        ).mock(return_value=Response(200, json=mock_products))

        client.list_products(
            search="widget",
            category="electronics",
            sku="TEST-001",
            in_stock=True,
            min_price=10.0,
            max_price=100.0,
        )

        assert route.called
        request = route.calls[0].request
        assert b"search=widget" in request.url.query
        assert b"category=electronics" in request.url.query
        assert b"sku=TEST-001" in request.url.query
        assert b"stock_status=instock" in request.url.query
        assert b"min_price=10.0" in request.url.query
        assert b"max_price=100.0" in request.url.query

    @respx.mock
    def test_get_product_success(self, client):
        """Test getting a specific product."""
        mock_product = {
            "id": 123,
            "name": "Test Product",
            "price": "49.99",
        }
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/products/123"
        ).mock(return_value=Response(200, json=mock_product))

        result = client.get_product(123)

        assert result == mock_product
        assert route.called

    @respx.mock
    def test_get_product_by_sku_found(self, client):
        """Test getting product by SKU when found."""
        mock_products = [
            {
                "id": 123,
                "name": "Test Product",
                "sku": "TEST-001",
            }
        ]
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/products"
        ).mock(return_value=Response(200, json=mock_products))

        result = client.get_product_by_sku("TEST-001")

        assert result == mock_products[0]
        assert route.called

    @respx.mock
    def test_get_product_by_sku_not_found(self, client):
        """Test getting product by SKU when not found."""
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/products"
        ).mock(return_value=Response(200, json=[]))

        result = client.get_product_by_sku("NONEXISTENT")

        assert result is None
        assert route.called


class TestCustomers:
    """Test customer operations."""

    @respx.mock
    def test_list_customers_success(self, client):
        """Test listing customers."""
        mock_customers = [
            {
                "id": 1,
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
            }
        ]
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/customers"
        ).mock(return_value=Response(200, json=mock_customers))

        result = client.list_customers(per_page=10)

        assert result["customers"] == mock_customers
        assert route.called

    @respx.mock
    def test_list_customers_by_email(self, client):
        """Test listing customers filtered by email."""
        mock_customers = [
            {
                "id": 1,
                "email": "test@example.com",
            }
        ]
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/customers"
        ).mock(return_value=Response(200, json=mock_customers))

        client.list_customers(email="test@example.com")

        assert route.called
        request = route.calls[0].request
        assert b"email=test%40example.com" in request.url.query

    @respx.mock
    def test_get_customer_success(self, client):
        """Test getting a specific customer."""
        mock_customer = {
            "id": 123,
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/customers/123"
        ).mock(return_value=Response(200, json=mock_customer))

        result = client.get_customer(123)

        assert result == mock_customer
        assert route.called

    @respx.mock
    def test_get_customer_by_email_found(self, client):
        """Test getting customer by email when found."""
        mock_customers = [
            {
                "id": 123,
                "email": "test@example.com",
            }
        ]
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/customers"
        ).mock(return_value=Response(200, json=mock_customers))

        result = client.get_customer_by_email("test@example.com")

        assert result == mock_customers[0]
        assert route.called

    @respx.mock
    def test_get_customer_by_email_not_found(self, client):
        """Test getting customer by email when not found."""
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/customers"
        ).mock(return_value=Response(200, json=[]))

        result = client.get_customer_by_email("nonexistent@example.com")

        assert result is None
        assert route.called

    @respx.mock
    def test_create_customer_success(self, client):
        """Test creating a customer."""
        mock_customer = {
            "id": 456,
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "Customer",
        }
        route = respx.post(
            "https://test-store.com/wp-json/wc/v3/customers"
        ).mock(return_value=Response(201, json=mock_customer))

        customer_data = {
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "Customer",
        }
        result = client.create_customer(customer_data)

        assert result == mock_customer
        assert route.called


class TestErrorHandling:
    """Test error handling."""

    @respx.mock
    def test_woocommerce_api_error(self, client):
        """Test handling WooCommerce API error response."""
        error_response = {
            "code": "woocommerce_rest_order_invalid_id",
            "message": "Invalid order ID",
            "data": {"status": 404},
        }
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/orders/999999"
        ).mock(return_value=Response(404, json=error_response))

        with pytest.raises(Exception) as exc_info:
            client.get_order(999999)

        assert "WooCommerce API Error" in str(exc_info.value)
        assert "woocommerce_rest_order_invalid_id" in str(exc_info.value)

    @respx.mock
    def test_http_error(self, client):
        """Test handling HTTP error."""
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(return_value=Response(500, text="Internal Server Error"))

        with pytest.raises(Exception) as exc_info:
            client.list_orders()

        assert "500" in str(exc_info.value)

    @respx.mock
    def test_connection_error(self, client):
        """Test handling connection error."""
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(side_effect=Exception("Connection failed"))

        with pytest.raises(Exception) as exc_info:
            client.list_orders()

        assert "Connection failed" in str(exc_info.value)

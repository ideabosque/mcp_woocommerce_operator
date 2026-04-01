#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unit tests for MCP WooCommerce Operator tools."""
import logging
from unittest.mock import MagicMock, patch

import pytest
import respx
from httpx import Response

from mcp_woocommerce_operator import MCPWooCommerceOperator


@pytest.fixture
def logger():
    """Create test logger."""
    return logging.getLogger("test")


@pytest.fixture
def settings():
    """Create test settings."""
    return {
        "woocommerce_url": "https://test-store.com",
        "consumer_key": "ck_test_key",
        "consumer_secret": "cs_test_secret",
    }


@pytest.fixture
def operator(logger, settings):
    """Create MCPWooCommerceOperator instance."""
    return MCPWooCommerceOperator(logger=logger, **settings)


class TestListOrders:
    """Test list_orders tool."""

    @respx.mock
    def test_list_orders_success(self, operator):
        """Test listing orders successfully."""
        mock_orders = [
            {
                "id": 1,
                "status": "processing",
                "total": "99.99",
                "customerId": 45,
            }
        ]
        respx.get(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(return_value=Response(200, json=mock_orders))

        result = operator.list_orders(status="processing")

        assert result["orders"][0]["id"] == 1
        assert result["orders"][0]["status"] == "processing"

    @respx.mock
    def test_list_orders_with_pagination(self, operator):
        """Test listing orders with pagination."""
        mock_orders = []
        route = respx.get(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(return_value=Response(200, json=mock_orders))

        result = operator.list_orders(page=2, per_page=50)

        assert result["page"] == 2


class TestGetOrder:
    """Test get_order tool."""

    @respx.mock
    def test_get_order_success(self, operator):
        """Test getting order successfully."""
        mock_order = {
            "id": 123,
            "status": "completed",
            "total": "149.99",
            "lineItems": [],
        }
        respx.get(
            "https://test-store.com/wp-json/wc/v3/orders/123"
        ).mock(return_value=Response(200, json=mock_order))

        result = operator.get_order(order_id=123)

        assert result["id"] == 123
        assert result["status"] == "completed"

    def test_get_order_missing_id(self, operator):
        """Test getting order without order_id."""
        with pytest.raises(Exception) as exc_info:
            operator.get_order()

        assert "order_id is required" in str(exc_info.value)


class TestCreateOrder:
    """Test create_order tool."""

    @respx.mock
    def test_create_order_with_customer_id(self, operator):
        """Test creating order with customer_id."""
        mock_order = {
            "id": 456,
            "status": "pending",
            "total": "99.99",
        }
        respx.post(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(return_value=Response(201, json=mock_order))

        result = operator.create_order(
            customer_id=123,
            line_items=[{"product_id": 1, "quantity": 2}],
        )

        assert result["id"] == 456

    @respx.mock
    def test_create_order_with_email(self, operator):
        """Test creating order with customer_email."""
        mock_order = {
            "id": 456,
            "status": "pending",
            "total": "99.99",
        }
        respx.post(
            "https://test-store.com/wp-json/wc/v3/orders"
        ).mock(return_value=Response(201, json=mock_order))

        result = operator.create_order(
            customer_email="test@example.com",
            customer_first_name="Test",
            customer_last_name="User",
            line_items=[{"product_id": 1, "quantity": 2}],
            billing_address={"address_1": "123 Main St"},
        )

        assert result["id"] == 456

    def test_create_order_missing_line_items(self, operator):
        """Test creating order without line_items."""
        with pytest.raises(Exception) as exc_info:
            operator.create_order(customer_id=123)

        assert "line_items is required" in str(exc_info.value)

    def test_create_order_invalid_email(self, operator):
        """Test creating order with invalid email."""
        with pytest.raises(Exception) as exc_info:
            operator.create_order(
                customer_email="invalid-email",
                line_items=[{"product_id": 1, "quantity": 2}],
            )

        assert "Invalid email format" in str(exc_info.value)


class TestUpdateOrderStatus:
    """Test update_order_status tool."""

    @respx.mock
    def test_update_order_status_success(self, operator):
        """Test updating order status."""
        mock_order = {
            "id": 123,
            "status": "completed",
        }
        respx.put(
            "https://test-store.com/wp-json/wc/v3/orders/123"
        ).mock(return_value=Response(200, json=mock_order))

        result = operator.update_order_status(order_id=123, status="completed")

        assert result["status"] == "completed"

    def test_update_order_status_invalid_status(self, operator):
        """Test updating order with invalid status."""
        with pytest.raises(Exception) as exc_info:
            operator.update_order_status(order_id=123, status="invalid_status")

        assert "Invalid status" in str(exc_info.value)


class TestListProducts:
    """Test list_products tool."""

    @respx.mock
    def test_list_products_success(self, operator):
        """Test listing products."""
        mock_products = [
            {
                "id": 1,
                "name": "Test Product",
                "sku": "TEST-001",
                "price": "49.99",
            }
        ]
        respx.get(
            "https://test-store.com/wp-json/wc/v3/products"
        ).mock(return_value=Response(200, json=mock_products))

        result = operator.list_products(search="test")

        assert result["products"][0]["name"] == "Test Product"


class TestGetProduct:
    """Test get_product tool."""

    @respx.mock
    def test_get_product_by_id(self, operator):
        """Test getting product by ID."""
        mock_product = {
            "id": 123,
            "name": "Test Product",
            "sku": "TEST-001",
        }
        respx.get(
            "https://test-store.com/wp-json/wc/v3/products/123"
        ).mock(return_value=Response(200, json=mock_product))

        result = operator.get_product(product_id=123)

        assert result["id"] == 123

    @respx.mock
    def test_get_product_by_sku(self, operator):
        """Test getting product by SKU."""
        mock_products = [
            {
                "id": 123,
                "name": "Test Product",
                "sku": "TEST-001",
            }
        ]
        respx.get(
            "https://test-store.com/wp-json/wc/v3/products"
        ).mock(return_value=Response(200, json=mock_products))

        result = operator.get_product(sku="TEST-001")

        assert result["sku"] == "TEST-001"

    def test_get_product_missing_params(self, operator):
        """Test getting product without ID or SKU."""
        with pytest.raises(Exception) as exc_info:
            operator.get_product()

        assert "Either product_id or sku is required" in str(exc_info.value)


class TestCreateCustomer:
    """Test create_customer tool."""

    @respx.mock
    def test_create_customer_success(self, operator):
        """Test creating customer."""
        mock_customer = {
            "id": 456,
            "email": "new@example.com",
            "first_name": "New",
            "last_name": "Customer",
        }
        respx.post(
            "https://test-store.com/wp-json/wc/v3/customers"
        ).mock(return_value=Response(201, json=mock_customer))

        result = operator.create_customer(
            email="new@example.com",
            first_name="New",
            last_name="Customer",
        )

        assert result["id"] == 456

    def test_create_customer_missing_required(self, operator):
        """Test creating customer without required fields."""
        with pytest.raises(Exception) as exc_info:
            operator.create_customer(email="test@example.com")

        assert "first_name is required" in str(exc_info.value)


class TestGetCustomer:
    """Test get_customer tool."""

    @respx.mock
    def test_get_customer_by_id(self, operator):
        """Test getting customer by ID."""
        mock_customer = {
            "id": 123,
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }
        respx.get(
            "https://test-store.com/wp-json/wc/v3/customers/123"
        ).mock(return_value=Response(200, json=mock_customer))

        result = operator.get_customer(customer_id=123)

        assert result["id"] == 123

    @respx.mock
    def test_get_customer_by_email(self, operator):
        """Test getting customer by email."""
        mock_customers = [
            {
                "id": 123,
                "email": "test@example.com",
                "first_name": "Test",
                "last_name": "User",
            }
        ]
        respx.get(
            "https://test-store.com/wp-json/wc/v3/customers"
        ).mock(return_value=Response(200, json=mock_customers))

        result = operator.get_customer(email="test@example.com")

        assert result["email"] == "test@example.com"

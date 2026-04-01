#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WooCommerce API client wrapper for MCP module."""
from __future__ import annotations

import base64
import logging
import traceback
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx

__author__ = "bibow"


class WooCommerceClient:
    """Client for interacting with WooCommerce REST API."""

    def __init__(
        self,
        logger: logging.Logger,
        woocommerce_url: str,
        consumer_key: str,
        consumer_secret: str,
        api_version: str = "wc/v3",
        verify_ssl: bool = True,
        timeout: int = 30,
        query_string_auth: bool = False,
    ):
        """Initialize WooCommerce client.

        Args:
            logger: Logger instance
            woocommerce_url: Base URL of WooCommerce store (e.g., https://store.com)
            consumer_key: WooCommerce consumer key
            consumer_secret: WooCommerce consumer secret
            api_version: API version (default: wc/v3)
            verify_ssl: Whether to verify SSL certificates
            timeout: Request timeout in seconds
            query_string_auth: Use query string auth instead of Basic Auth
        """
        self.logger = logger
        self.woocommerce_url = woocommerce_url.rstrip("/")
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_version = api_version
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.query_string_auth = query_string_auth
        self.base_url = f"{self.woocommerce_url}/wp-json/{self.api_version}"

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if self.query_string_auth:
            return {}

        credentials = base64.b64encode(
            f"{self.consumer_key}:{self.consumer_secret}".encode()
        ).decode()
        return {"Authorization": f"Basic {credentials}"}

    def _get_query_params(self) -> Dict[str, str]:
        """Get query string authentication parameters."""
        if not self.query_string_auth:
            return {}
        return {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret,
        }

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP request to WooCommerce API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., 'orders', 'products/123')
            params: Query parameters
            data: Request body data

        Returns:
            Parsed JSON response

        Raises:
            Exception: On API errors
        """
        url = f"{self.base_url}/{endpoint}"

        # Add query string auth if enabled
        request_params = {**self._get_query_params()}
        if params:
            request_params.update(params)

        # Build query string
        if request_params:
            url = f"{url}?{urlencode(request_params, doseq=True)}"

        headers = {
            "Content-Type": "application/json",
            **self._get_auth_headers(),
        }

        try:
            self.logger.debug(f"Making {method} request to {url}")

            with httpx.Client(
                http2=True,
                timeout=httpx.Timeout(self.timeout),
                verify=self.verify_ssl,
            ) as client:
                if method.upper() == "GET":
                    response = client.get(url, headers=headers)
                elif method.upper() == "POST":
                    response = client.post(url, headers=headers, json=data)
                elif method.upper() == "PUT":
                    response = client.put(url, headers=headers, json=data)
                elif method.upper() == "DELETE":
                    response = client.delete(url, headers=headers)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()

            if response.status_code == 204:
                return {}

            result = response.json()

            # Check for WooCommerce error response
            if isinstance(result, dict) and "code" in result and "message" in result:
                error_code = result.get("code", "unknown")
                error_message = result.get("message", "Unknown error")
                raise Exception(f"WooCommerce API Error [{error_code}]: {error_message}")

            return result

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = f" - {error_body.get('message', '')}"
            except:
                error_detail = f" - {e.response.text}"

            self.logger.error(f"HTTP error {e.response.status_code}{error_detail}")
            raise Exception(f"HTTP {e.response.status_code}: {e}{error_detail}")

        except httpx.RequestError as e:
            self.logger.error(f"Request error: {e}")
            raise Exception(f"Request failed: {e}")

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise

    # ============== Orders ==============

    def list_orders(
        self,
        status: Optional[str] = None,
        customer_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        """List WooCommerce orders with filters.

        Args:
            status: Order status filter
            customer_id: Filter by customer ID
            date_from: Start date (ISO 8601)
            date_to: End date (ISO 8601)
            page: Page number
            per_page: Items per page

        Returns:
            Dict with orders list and metadata
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if status:
            params["status"] = status
        if customer_id:
            params["customer"] = customer_id
        if date_from:
            params["after"] = date_from
        if date_to:
            params["before"] = date_to

        result = self._make_request("GET", "orders", params=params)

        return {
            "orders": result if isinstance(result, list) else [],
            "page": page,
            "per_page": per_page,
        }

    def get_order(self, order_id: int) -> Dict[str, Any]:
        """Get a specific order by ID.

        Args:
            order_id: WooCommerce order ID

        Returns:
            Order details
        """
        return self._make_request("GET", f"orders/{order_id}")

    def create_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order.

        Args:
            order_data: Order data dict

        Returns:
            Created order details
        """
        return self._make_request("POST", "orders", data=order_data)

    def update_order(self, order_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing order.

        Args:
            order_id: Order ID to update
            order_data: Updated order data

        Returns:
            Updated order details
        """
        return self._make_request("PUT", f"orders/{order_id}", data=order_data)

    # ============== Products ==============

    def list_products(
        self,
        search: Optional[str] = None,
        category: Optional[str] = None,
        sku: Optional[str] = None,
        in_stock: Optional[bool] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        """List WooCommerce products with filters.

        Args:
            search: Search term
            category: Category ID or slug
            sku: Filter by SKU
            in_stock: Filter by stock status
            min_price: Minimum price
            max_price: Maximum price
            page: Page number
            per_page: Items per page

        Returns:
            Dict with products list and metadata
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if search:
            params["search"] = search
        if category:
            params["category"] = category
        if sku:
            params["sku"] = sku
        if in_stock is not None:
            params["stock_status"] = "instock" if in_stock else "outofstock"
        if min_price is not None:
            params["min_price"] = str(min_price)
        if max_price is not None:
            params["max_price"] = str(max_price)

        result = self._make_request("GET", "products", params=params)

        return {
            "products": result if isinstance(result, list) else [],
            "page": page,
            "per_page": per_page,
        }

    def get_product(self, product_id: int) -> Dict[str, Any]:
        """Get a specific product by ID.

        Args:
            product_id: Product ID

        Returns:
            Product details
        """
        return self._make_request("GET", f"products/{product_id}")

    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get a product by SKU.

        Args:
            sku: Product SKU

        Returns:
            Product details or None if not found
        """
        result = self.list_products(sku=sku, per_page=1)
        products = result.get("products", [])
        return products[0] if products else None

    # ============== Customers ==============

    def list_customers(
        self,
        email: Optional[str] = None,
        page: int = 1,
        per_page: int = 10,
    ) -> Dict[str, Any]:
        """List WooCommerce customers.

        Args:
            email: Filter by email
            page: Page number
            per_page: Items per page

        Returns:
            Dict with customers list
        """
        params: Dict[str, Any] = {
            "page": page,
            "per_page": per_page,
        }

        if email:
            params["email"] = email

        result = self._make_request("GET", "customers", params=params)

        return {
            "customers": result if isinstance(result, list) else [],
            "page": page,
            "per_page": per_page,
        }

    def get_customer(self, customer_id: int) -> Dict[str, Any]:
        """Get a specific customer by ID.

        Args:
            customer_id: Customer ID

        Returns:
            Customer details
        """
        return self._make_request("GET", f"customers/{customer_id}")

    def get_customer_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get a customer by email address.

        Args:
            email: Customer email

        Returns:
            Customer details or None if not found
        """
        result = self.list_customers(email=email, per_page=1)
        customers = result.get("customers", [])
        return customers[0] if customers else None

    def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer.

        Args:
            customer_data: Customer data dict

        Returns:
            Created customer details
        """
        return self._make_request("POST", "customers", data=customer_data)

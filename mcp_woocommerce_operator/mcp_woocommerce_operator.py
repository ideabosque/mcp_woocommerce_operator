#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MCP WooCommerce Operator - Main MCP module with tools."""
from __future__ import annotations

import logging
import re
import traceback
from typing import Any, Dict, List, Optional

import humps

from .woocommerce_client import WooCommerceClient

__author__ = "bibow"


MCP_CONFIGURATION = {
    "tools": [
        {
            "name": "list_orders",
            "description": "Retrieve WooCommerce orders with filtering options. Supports filtering by status (pending, processing, completed, cancelled, etc.), customer ID, and date range. Returns paginated list of orders with basic information.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Order status filter (pending, processing, completed, cancelled, refunded, failed, trash)",
                    },
                    "customer_id": {
                        "type": "number",
                        "description": "Filter by customer ID",
                    },
                    "date_from": {
                        "type": "string",
                        "description": "Start date in ISO 8601 format (e.g., 2024-03-01T00:00:00Z)",
                    },
                    "date_to": {
                        "type": "string",
                        "description": "End date in ISO 8601 format",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number (default: 1)",
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Items per page, max 100 (default: 10)",
                    },
                },
            },
            "annotations": None,
        },
        {
            "name": "get_order",
            "description": "Get detailed information about a specific WooCommerce order by ID. Returns complete order details including line items, shipping and billing addresses, customer information, payment method, and order metadata.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "number",
                        "description": "WooCommerce order ID",
                    },
                },
                "required": ["order_id"],
            },
            "annotations": None,
        },
        {
            "name": "create_order",
            "description": "Create a new order in WooCommerce. Supports creating orders for existing customers (via customer_id) or new customers (via email and name). Requires line_items array with at least one product. Returns the created order with order_id and status.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "number",
                        "description": "Existing customer ID (optional, if not provided customer_email is required)",
                    },
                    "customer_email": {
                        "type": "string",
                        "description": "Customer email (required if customer_id not provided)",
                    },
                    "customer_first_name": {
                        "type": "string",
                        "description": "Customer first name",
                    },
                    "customer_last_name": {
                        "type": "string",
                        "description": "Customer last name",
                    },
                    "billing_address": {
                        "type": "object",
                        "description": "Billing address",
                        "properties": {
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "company": {"type": "string"},
                            "address_1": {"type": "string"},
                            "address_2": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "postcode": {"type": "string"},
                            "country": {"type": "string"},
                            "email": {"type": "string"},
                            "phone": {"type": "string"},
                        },
                    },
                    "shipping_address": {
                        "type": "object",
                        "description": "Shipping address (if not provided, billing_address is used)",
                        "properties": {
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "company": {"type": "string"},
                            "address_1": {"type": "string"},
                            "address_2": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "postcode": {"type": "string"},
                            "country": {"type": "string"},
                        },
                    },
                    "line_items": {
                        "type": "array",
                        "description": "Line items (required, at least one item)",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "number"},
                                "variation_id": {"type": "number"},
                                "quantity": {"type": "number"},
                                "price": {"type": "number"},
                            },
                            "required": ["product_id", "quantity"],
                        },
                    },
                    "shipping_lines": {
                        "type": "array",
                        "description": "Shipping lines",
                        "items": {
                            "type": "object",
                            "properties": {
                                "method_id": {"type": "string"},
                                "method_title": {"type": "string"},
                                "total": {"type": "string"},
                            },
                        },
                    },
                    "coupon_lines": {
                        "type": "array",
                        "description": "Coupon codes to apply",
                        "items": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string"},
                            },
                        },
                    },
                    "payment_method": {
                        "type": "string",
                        "description": "Payment method ID (e.g., bacs, cod, paypal)",
                    },
                    "set_paid": {
                        "type": "boolean",
                        "description": "Mark order as paid immediately",
                    },
                    "customer_note": {
                        "type": "string",
                        "description": "Customer note for the order",
                    },
                },
                "required": ["line_items"],
            },
            "annotations": None,
        },
        {
            "name": "update_order_status",
            "description": "Update the status of an existing WooCommerce order. Common statuses: pending, processing, completed, cancelled, refunded, failed, on-hold. Optionally add a private note to the order.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "number",
                        "description": "Order ID to update",
                    },
                    "status": {
                        "type": "string",
                        "description": "New status (pending, processing, completed, cancelled, refunded, failed, on-hold)",
                    },
                    "note": {
                        "type": "string",
                        "description": "Private note to add to order (optional)",
                    },
                },
                "required": ["order_id", "status"],
            },
            "annotations": None,
        },
        {
            "name": "list_products",
            "description": "Search and list WooCommerce products with various filters. Supports filtering by search term, category, SKU, stock status, and price range. Returns paginated list of products with basic information.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "search": {
                        "type": "string",
                        "description": "Search term",
                    },
                    "category": {
                        "type": "string",
                        "description": "Category ID or slug",
                    },
                    "sku": {
                        "type": "string",
                        "description": "Filter by SKU",
                    },
                    "in_stock": {
                        "type": "boolean",
                        "description": "Filter by stock status",
                    },
                    "min_price": {
                        "type": "number",
                        "description": "Minimum price",
                    },
                    "max_price": {
                        "type": "number",
                        "description": "Maximum price",
                    },
                    "page": {
                        "type": "number",
                        "description": "Page number (default: 1)",
                    },
                    "per_page": {
                        "type": "number",
                        "description": "Items per page, max 100 (default: 10)",
                    },
                },
            },
            "annotations": None,
        },
        {
            "name": "get_product",
            "description": "Get detailed product information by ID or SKU. Returns complete product details including price, stock status, variations, attributes, categories, and images.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "product_id": {
                        "type": "number",
                        "description": "Product ID",
                    },
                    "sku": {
                        "type": "string",
                        "description": "Product SKU (alternative to product_id)",
                    },
                },
                "anyOf": [{"required": ["product_id"]}, {"required": ["sku"]}],
            },
            "annotations": None,
        },
        {
            "name": "create_customer",
            "description": "Create a new WooCommerce customer account. Generates a username automatically if not provided. Optionally set billing and shipping addresses. Returns customer ID and details.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Customer email (required)",
                    },
                    "first_name": {
                        "type": "string",
                        "description": "First name (required)",
                    },
                    "last_name": {
                        "type": "string",
                        "description": "Last name (required)",
                    },
                    "username": {
                        "type": "string",
                        "description": "Username (auto-generated if not provided)",
                    },
                    "password": {
                        "type": "string",
                        "description": "Password (auto-generated if not provided)",
                    },
                    "billing": {
                        "type": "object",
                        "description": "Billing address",
                        "properties": {
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "company": {"type": "string"},
                            "address_1": {"type": "string"},
                            "address_2": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "postcode": {"type": "string"},
                            "country": {"type": "string"},
                            "email": {"type": "string"},
                            "phone": {"type": "string"},
                        },
                    },
                    "shipping": {
                        "type": "object",
                        "description": "Shipping address",
                        "properties": {
                            "first_name": {"type": "string"},
                            "last_name": {"type": "string"},
                            "company": {"type": "string"},
                            "address_1": {"type": "string"},
                            "address_2": {"type": "string"},
                            "city": {"type": "string"},
                            "state": {"type": "string"},
                            "postcode": {"type": "string"},
                            "country": {"type": "string"},
                        },
                    },
                },
                "required": ["email", "first_name", "last_name"],
            },
            "annotations": None,
        },
        {
            "name": "get_customer",
            "description": "Get customer information by ID or email. Returns customer details including billing/shipping addresses and order count.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "number",
                        "description": "Customer ID",
                    },
                    "email": {
                        "type": "string",
                        "description": "Customer email (alternative to customer_id)",
                    },
                },
                "anyOf": [{"required": ["customer_id"]}, {"required": ["email"]}],
            },
            "annotations": None,
        },
    ],
    "resources": [],
    "prompts": [],
    "module_links": [
        {
            "type": "tool",
            "name": "list_orders",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "function_name": "list_orders",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "get_order",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "function_name": "get_order",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "create_order",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "function_name": "create_order",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "update_order_status",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "function_name": "update_order_status",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "list_products",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "function_name": "list_products",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "get_product",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "function_name": "get_product",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "create_customer",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "function_name": "create_customer",
            "return_type": "text",
        },
        {
            "type": "tool",
            "name": "get_customer",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "function_name": "get_customer",
            "return_type": "text",
        },
    ],
    "modules": [
        {
            "package_name": "mcp_woocommerce_operator",
            "module_name": "mcp_woocommerce_operator",
            "class_name": "MCPWooCommerceOperator",
            "setting": {
                "keyword": "woocommerce",
                "woocommerce_url": "https://store.example.com",
                "consumer_key": "ck_...",
                "consumer_secret": "cs_...",
                "api_version": "wc/v3",
                "verify_ssl": True,
                "timeout": 30,
                "query_string_auth": False,
            },
        }
    ],
}


class MCPWooCommerceOperator:
    """MCP WooCommerce Operator - Provides MCP tools for WooCommerce integration."""

    def __init__(self, logger: logging.Logger, **setting: Dict[str, Any]):
        """Initialize MCP WooCommerce Operator.

        Args:
            logger: Logger instance
            **setting: Configuration settings including:
                - woocommerce_url: Store URL
                - consumer_key: API consumer key
                - consumer_secret: API consumer secret
                - api_version: API version (default: wc/v3)
                - verify_ssl: SSL verification (default: True)
                - timeout: Request timeout (default: 30)
                - query_string_auth: Use query string auth (default: False)
        """
        self.logger = logger
        self.setting = setting
        self._client: Optional[WooCommerceClient] = None

    def _get_client(self) -> WooCommerceClient:
        """Get or create WooCommerce client instance."""
        if self._client is None:
            required_keys = ["woocommerce_url", "consumer_key", "consumer_secret"]
            for key in required_keys:
                if not self.setting.get(key):
                    raise ValueError(f"Missing required setting: {key}")

            self._client = WooCommerceClient(
                logger=self.logger,
                woocommerce_url=self.setting["woocommerce_url"],
                consumer_key=self.setting["consumer_key"],
                consumer_secret=self.setting["consumer_secret"],
                api_version=self.setting.get("api_version", "wc/v3"),
                verify_ssl=self.setting.get("verify_ssl", True),
                timeout=self.setting.get("timeout", 30),
                query_string_auth=self.setting.get("query_string_auth", False),
            )
        return self._client

    def _validate_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    # ============== Orders ==============

    def list_orders(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List orders with filtering."""
        try:
            self.logger.info(f"list_orders called with arguments: {arguments}")

            # Extract and validate parameters
            status = arguments.get("status")
            customer_id = arguments.get("customer_id")
            date_from = arguments.get("date_from")
            date_to = arguments.get("date_to")
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 10)

            # Validate page and per_page
            if not isinstance(page, int) or page < 1:
                page = 1
            if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
                per_page = 10

            client = self._get_client()
            result = client.list_orders(
                status=status,
                customer_id=customer_id,
                date_from=date_from,
                date_to=date_to,
                page=page,
                per_page=per_page,
            )

            # Convert to snake_case for consistency
            result["orders"] = [humps.decamelize(order) for order in result["orders"]]

            return result

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(f"Failed to list orders: {e}")

    def get_order(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get order details by ID."""
        try:
            self.logger.info(f"get_order called with arguments: {arguments}")

            order_id = arguments.get("order_id")
            if not order_id:
                raise ValueError("order_id is required")

            if not isinstance(order_id, int) or order_id < 1:
                raise ValueError("order_id must be a positive integer")

            client = self._get_client()
            result = client.get_order(order_id)

            return humps.decamelize(result)

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(f"Failed to get order: {e}")

    def create_order(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new order."""
        try:
            self.logger.info(f"create_order called with arguments: {arguments}")

            # Validate required fields
            line_items = arguments.get("line_items", [])
            if not line_items:
                raise ValueError("line_items is required and must contain at least one item")

            # Build order data
            order_data: Dict[str, Any] = {
                "line_items": line_items,
            }

            # Add customer information
            if arguments.get("customer_id"):
                order_data["customer_id"] = arguments["customer_id"]
            elif arguments.get("customer_email"):
                email = arguments["customer_email"]
                if not self._validate_email(email):
                    raise ValueError(f"Invalid email format: {email}")

                order_data["billing"] = {
                    "email": email,
                }

                if arguments.get("customer_first_name"):
                    order_data["billing"]["first_name"] = arguments["customer_first_name"]
                if arguments.get("customer_last_name"):
                    order_data["billing"]["last_name"] = arguments["customer_last_name"]
            else:
                raise ValueError("Either customer_id or customer_email is required")

            # Add billing address
            if arguments.get("billing_address"):
                if "billing" not in order_data:
                    order_data["billing"] = {}
                order_data["billing"].update(arguments["billing_address"])

            # Add shipping address
            if arguments.get("shipping_address"):
                order_data["shipping"] = arguments["shipping_address"]
            elif arguments.get("billing_address"):
                # Use billing as shipping if not provided
                order_data["shipping"] = arguments["billing_address"]

            # Add shipping lines
            if arguments.get("shipping_lines"):
                order_data["shipping_lines"] = arguments["shipping_lines"]

            # Add coupon lines
            if arguments.get("coupon_lines"):
                order_data["coupon_lines"] = arguments["coupon_lines"]

            # Add payment method
            if arguments.get("payment_method"):
                order_data["payment_method"] = arguments["payment_method"]
                order_data["payment_method_title"] = (
                    arguments["payment_method"].replace("_", " ").title()
                )

            # Set paid status
            if arguments.get("set_paid"):
                order_data["set_paid"] = True

            # Add customer note
            if arguments.get("customer_note"):
                order_data["customer_note"] = arguments["customer_note"]

            client = self._get_client()
            result = client.create_order(order_data)

            return humps.decamelize(result)

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(f"Failed to create order: {e}")

    def update_order_status(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update order status."""
        try:
            self.logger.info(f"update_order_status called with arguments: {arguments}")

            order_id = arguments.get("order_id")
            status = arguments.get("status")

            if not order_id:
                raise ValueError("order_id is required")
            if not status:
                raise ValueError("status is required")

            # Validate status
            valid_statuses = [
                "pending",
                "processing",
                "completed",
                "cancelled",
                "refunded",
                "failed",
                "on-hold",
            ]
            if status not in valid_statuses:
                raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

            update_data: Dict[str, Any] = {"status": status}

            # Add note if provided
            if arguments.get("note"):
                update_data["customer_note"] = arguments["note"]

            client = self._get_client()
            result = client.update_order(order_id, update_data)

            return humps.decamelize(result)

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(f"Failed to update order status: {e}")

    # ============== Products ==============

    def list_products(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List products with filtering."""
        try:
            self.logger.info(f"list_products called with arguments: {arguments}")

            search = arguments.get("search")
            category = arguments.get("category")
            sku = arguments.get("sku")
            in_stock = arguments.get("in_stock")
            min_price = arguments.get("min_price")
            max_price = arguments.get("max_price")
            page = arguments.get("page", 1)
            per_page = arguments.get("per_page", 10)

            # Validate page and per_page
            if not isinstance(page, int) or page < 1:
                page = 1
            if not isinstance(per_page, int) or per_page < 1 or per_page > 100:
                per_page = 10

            client = self._get_client()
            result = client.list_products(
                search=search,
                category=category,
                sku=sku,
                in_stock=in_stock,
                min_price=min_price,
                max_price=max_price,
                page=page,
                per_page=per_page,
            )

            # Convert to snake_case for consistency
            result["products"] = [humps.decamelize(product) for product in result["products"]]

            return result

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(f"Failed to list products: {e}")

    def get_product(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get product by ID or SKU."""
        try:
            self.logger.info(f"get_product called with arguments: {arguments}")

            product_id = arguments.get("product_id")
            sku = arguments.get("sku")

            if not product_id and not sku:
                raise ValueError("Either product_id or sku is required")

            client = self._get_client()

            if product_id:
                result = client.get_product(product_id)
            else:
                result = client.get_product_by_sku(sku)
                if not result:
                    raise Exception(f"Product with SKU '{sku}' not found")

            return humps.decamelize(result)

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(f"Failed to get product: {e}")

    # ============== Customers ==============

    def create_customer(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer."""
        try:
            self.logger.info(f"create_customer called with arguments: {arguments}")

            email = arguments.get("email")
            first_name = arguments.get("first_name")
            last_name = arguments.get("last_name")

            # Validate required fields
            if not email:
                raise ValueError("email is required")
            if not first_name:
                raise ValueError("first_name is required")
            if not last_name:
                raise ValueError("last_name is required")

            # Validate email format
            if not self._validate_email(email):
                raise ValueError(f"Invalid email format: {email}")

            customer_data: Dict[str, Any] = {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            }

            # Add optional fields
            if arguments.get("username"):
                customer_data["username"] = arguments["username"]
            else:
                # Generate username from email
                customer_data["username"] = email.split("@")[0]

            if arguments.get("password"):
                customer_data["password"] = arguments["password"]

            if arguments.get("billing"):
                customer_data["billing"] = arguments["billing"]

            if arguments.get("shipping"):
                customer_data["shipping"] = arguments["shipping"]

            client = self._get_client()
            result = client.create_customer(customer_data)

            return humps.decamelize(result)

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(f"Failed to create customer: {e}")

    def get_customer(self, **arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get customer by ID or email."""
        try:
            self.logger.info(f"get_customer called with arguments: {arguments}")

            customer_id = arguments.get("customer_id")
            email = arguments.get("email")

            if not customer_id and not email:
                raise ValueError("Either customer_id or email is required")

            client = self._get_client()

            if customer_id:
                result = client.get_customer(customer_id)
            else:
                # Validate email format
                if not self._validate_email(email):
                    raise ValueError(f"Invalid email format: {email}")

                result = client.get_customer_by_email(email)
                if not result:
                    raise Exception(f"Customer with email '{email}' not found")

            return humps.decamelize(result)

        except Exception as e:
            log = traceback.format_exc()
            self.logger.error(log)
            raise Exception(f"Failed to get customer: {e}")

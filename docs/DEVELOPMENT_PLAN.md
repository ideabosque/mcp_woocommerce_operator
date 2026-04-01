# MCP WooCommerce Operator - Development Plan

## Overview

Create an MCP (Model Context Protocol) module that provides AI agents with tools to interact with WooCommerce stores, including reading orders, placing orders, and managing products.

## Architecture

### Directory Structure
```
mcp_woocommerce_operator/
├── mcp_woocommerce_operator/
│   ├── __init__.py           # Package exports
│   ├── mcp_woocommerce_operator.py  # Main MCP class with tools
│   ├── woocommerce_client.py  # WooCommerce API client wrapper
│   └── graphql_module.py     # GraphQL integration (if needed)
├── docs/
│   ├── DEVELOPMENT_PLAN.md   # This file
│   ├── API_REFERENCE.md      # WooCommerce API documentation
│   └── EXAMPLES.md           # Usage examples
├── tests/
│   ├── __init__.py
│   ├── test_woocommerce_client.py
│   └── test_mcp_tools.py
├── pyproject.toml
├── README.md
└── .env.example
```

## Tools Specification

### 1. `list_orders`
**Purpose:** Retrieve WooCommerce orders with filtering options
**Input Schema:**
```json
{
  "status": "string (optional) - Order status (pending, processing, completed, cancelled)",
  "customer_id": "number (optional) - Filter by customer",
  "date_from": "string (optional) - ISO 8601 date",
  "date_to": "string (optional) - ISO 8601 date",
  "page": "number (optional) - Page number, default 1",
  "per_page": "number (optional) - Items per page, max 100"
}
```
**Returns:** List of orders with details (order_id, status, total, items, customer_info)

### 2. `get_order`
**Purpose:** Get detailed information about a specific order
**Input Schema:**
```json
{
  "order_id": "number (required) - WooCommerce order ID"
}
```
**Returns:** Complete order details including line items, shipping, billing, metadata

### 3. `create_order`
**Purpose:** Place a new order in WooCommerce
**Input Schema:**
```json
{
  "customer_id": "number (optional) - Existing customer ID",
  "customer_email": "string (required if no customer_id) - Customer email",
  "customer_first_name": "string (optional) - First name",
  "customer_last_name": "string (optional) - Last name",
  "billing_address": {
    "first_name": "string",
    "last_name": "string",
    "company": "string",
    "address_1": "string",
    "address_2": "string",
    "city": "string",
    "state": "string",
    "postcode": "string",
    "country": "string",
    "email": "string",
    "phone": "string"
  },
  "shipping_address": {
    "first_name": "string",
    "last_name": "string",
    "company": "string",
    "address_1": "string",
    "address_2": "string",
    "city": "string",
    "state": "string",
    "postcode": "string",
    "country": "string"
  },
  "line_items": [
    {
      "product_id": "number (required)",
      "variation_id": "number (optional)",
      "quantity": "number (required)",
      "price": "number (optional) - Override price"
    }
  ],
  "shipping_lines": [
    {
      "method_id": "string",
      "method_title": "string",
      "total": "string"
    }
  ],
  "coupon_lines": [
    {
      "code": "string"
    }
  ],
  "payment_method": "string (optional)",
  "set_paid": "boolean (optional) - Mark as paid",
  "customer_note": "string (optional)"
}
```
**Returns:** Created order details with order_id and status

### 4. `update_order_status`
**Purpose:** Update order status (e.g., processing, completed, cancelled)
**Input Schema:**
```json
{
  "order_id": "number (required)",
  "status": "string (required) - new status",
  "note": "string (optional) - Private note"
}
```
**Returns:** Updated order details

### 5. `list_products`
**Purpose:** Search and list WooCommerce products
**Input Schema:**
```json
{
  "search": "string (optional) - Search term",
  "category": "string (optional) - Category ID or slug",
  "sku": "string (optional) - Filter by SKU",
  "in_stock": "boolean (optional) - Filter by stock status",
  "min_price": "number (optional)",
  "max_price": "number (optional)",
  "page": "number (optional)",
  "per_page": "number (optional)"
}
```
**Returns:** List of products with id, name, sku, price, stock_status, categories

### 6. `get_product`
**Purpose:** Get detailed product information
**Input Schema:**
```json
{
  "product_id": "number (required) OR",
  "sku": "string (required) - Search by SKU"
}
```
**Returns:** Complete product details including variations, stock, attributes

### 7. `create_customer`
**Purpose:** Create a new WooCommerce customer
**Input Schema:**
```json
{
  "email": "string (required)",
  "first_name": "string (required)",
  "last_name": "string (required)",
  "username": "string (optional) - Auto-generated if not provided",
  "password": "string (optional) - Auto-generated if not provided",
  "billing": "object (optional) - Same structure as order billing",
  "shipping": "object (optional) - Same structure as order shipping"
}
```
**Returns:** Created customer details with customer_id

### 8. `get_customer`
**Purpose:** Retrieve customer information
**Input Schema:**
```json
{
  "customer_id": "number (optional) OR",
  "email": "string (optional)"
}
```
**Returns:** Customer details with orders history

## MCP Configuration

```python
MCP_CONFIGURATION = {
    "tools": [
        {"name": "list_orders", "description": "...", "inputSchema": {...}},
        {"name": "get_order", "description": "...", "inputSchema": {...}},
        {"name": "create_order", "description": "...", "inputSchema": {...}},
        {"name": "update_order_status", "description": "...", "inputSchema": {...}},
        {"name": "list_products", "description": "...", "inputSchema": {...}},
        {"name": "get_product", "description": "...", "inputSchema": {...}},
        {"name": "create_customer", "description": "...", "inputSchema": {...}},
        {"name": "get_customer", "description": "...", "inputSchema": {...}},
    ],
    "modules": [{
        "setting": {
            "woocommerce_url": "https://store.example.com",
            "consumer_key": "ck_...",
            "consumer_secret": "cs_...",
            "api_version": "wc/v3",
            "verify_ssl": True,
            "timeout": 30,
            "query_string_auth": False  # Use for HTTPS
        }
    }]
}
```

## Implementation Phases

### Phase 1: Foundation (Day 1-2)
1. Set up project structure
2. Create pyproject.toml with dependencies:
   - `httpx` or `requests` - HTTP client
   - `humps` - Case conversion
   - `silvaengine_utility` - GraphQL utilities (if needed)
3. Implement `WooCommerceClient` class
4. Basic error handling and logging

### Phase 2: Core Tools (Day 3-4)
1. Implement order reading tools:
   - `list_orders`
   - `get_order`
2. Implement product reading tools:
   - `list_products`
   - `get_product`
3. Write unit tests for reading operations

### Phase 3: Write Operations (Day 5-6)
1. Implement order creation:
   - `create_order`
   - `update_order_status`
2. Implement customer management:
   - `create_customer`
   - `get_customer`
3. Write comprehensive tests

### Phase 4: Integration & Documentation (Day 7)
1. Integration testing with real WooCommerce store
2. Documentation:
   - README.md
   - API_REFERENCE.md
   - EXAMPLES.md
3. Error handling refinement
4. Performance optimization

## Dependencies

```toml
[tool.poetry.dependencies]
python = ">=3.8"
httpx = "^0.24.0"  # or requests = "^2.31.0"
humps = "^0.2.2"
python-dotenv = "^1.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
respx = "^0.20.0"  # for mocking httpx
```

## API Integration

### WooCommerce REST API v3

**Base URL:** `{woocommerce_url}/wp-json/wc/v3/`

**Authentication:**
- OAuth 1.0a for HTTP
- Basic Auth for HTTPS (query string or header)

**Key Endpoints:**
- `GET /orders` - List orders
- `GET /orders/{id}` - Get order
- `POST /orders` - Create order
- `PUT /orders/{id}` - Update order
- `GET /products` - List products
- `GET /products/{id}` - Get product
- `POST /customers` - Create customer
- `GET /customers/{id}` - Get customer

## Error Handling Strategy

1. **Network Errors:** Retry with exponential backoff
2. **API Errors:** Parse WooCommerce error responses
3. **Validation Errors:** Validate inputs before API calls
4. **Authentication Errors:** Clear error messages for credential issues

## Testing Strategy

1. **Unit Tests:** Mock WooCommerce API responses
2. **Integration Tests:** Test against staging WooCommerce instance
3. **E2E Tests:** Full MCP tool invocation flows

## Configuration Example

```python
# settings
{
    "keyword": "woocommerce",
    "woocommerce_url": "https://mystore.com",
    "consumer_key": "ck_live_...",
    "consumer_secret": "cs_live_...",
    "api_version": "wc/v3",
    "verify_ssl": True,
    "timeout": 30
}
```

## Future Enhancements

1. **Batch Operations:** Process multiple orders at once
2. **Webhooks:** Receive real-time order updates
3. **Inventory Management:** Update stock levels
4. **Shipping Integration:** Calculate shipping rates
5. **Payment Gateways:** Support for specific payment methods
6. **Analytics:** Sales reports and metrics

## Security Considerations

1. Store credentials securely (environment variables)
2. Use HTTPS only for production
3. Validate all inputs to prevent injection
4. Rate limiting to avoid API throttling
5. Sanitize customer data in logs

## Success Criteria

- [ ] All 8 tools implemented and tested
- [ ] 90%+ test coverage
- [ ] Documentation complete
- [ ] Integration tests pass
- [ ] Error handling robust
- [ ] Performance benchmarks met (< 2s response time)

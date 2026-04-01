# MCP WooCommerce Operator Examples

## Example 1: List Recent Orders

```python
# MCP Tool Invocation
{
  "name": "list_orders",
  "arguments": {
    "status": "processing",
    "date_from": "2024-03-01T00:00:00Z",
    "per_page": 10
  }
}

# Response
{
  "orders": [
    {
      "order_id": 123,
      "status": "processing",
      "total": "99.99",
      "currency": "USD",
      "customer": {
        "id": 45,
        "email": "customer@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "line_items": [
        {
          "product_id": 56,
          "name": "Premium Widget",
          "quantity": 2,
          "price": "49.99"
        }
      ],
      "date_created": "2024-03-28T10:30:00Z"
    }
  ],
  "total_count": 25,
  "page": 1
}
```

## Example 2: Get Order Details

```python
# MCP Tool Invocation
{
  "name": "get_order",
  "arguments": {
    "order_id": 123
  }
}

# Response
{
  "order_id": 123,
  "order_key": "wc_order_abc123",
  "status": "completed",
  "total": "149.99",
  "subtotal": "139.99",
  "shipping_total": "10.00",
  "currency": "USD",
  "customer": {
    "id": 45,
    "email": "customer@example.com"
  },
  "billing": {
    "first_name": "John",
    "last_name": "Doe",
    "address_1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postcode": "10001",
    "country": "US"
  },
  "line_items": [...],
  "shipping_lines": [...]
}
```

## Example 3: Create New Order

```python
# MCP Tool Invocation
{
  "name": "create_order",
  "arguments": {
    "customer_email": "newcustomer@example.com",
    "customer_first_name": "Jane",
    "customer_last_name": "Smith",
    "billing_address": {
      "first_name": "Jane",
      "last_name": "Smith",
      "address_1": "456 Oak Ave",
      "city": "Los Angeles",
      "state": "CA",
      "postcode": "90001",
      "country": "US",
      "email": "newcustomer@example.com",
      "phone": "555-123-4567"
    },
    "line_items": [
      {
        "product_id": 101,
        "quantity": 1
      },
      {
        "product_id": 102,
        "quantity": 2
      }
    ],
    "shipping_lines": [
      {
        "method_id": "flat_rate",
        "method_title": "Standard Shipping",
        "total": "15.00"
      }
    ],
    "set_paid": false
  }
}

# Response
{
  "order_id": 456,
  "order_key": "wc_order_xyz789",
  "status": "pending",
  "total": "134.99",
  "customer_id": 67,
  "created_at": "2024-03-31T20:30:00Z"
}
```

## Example 4: Update Order Status

```python
# MCP Tool Invocation
{
  "name": "update_order_status",
  "arguments": {
    "order_id": 456,
    "status": "completed",
    "note": "Payment received via Stripe"
  }
}
```

## Example 5: Search Products

```python
# MCP Tool Invocation
{
  "name": "list_products",
  "arguments": {
    "search": "widget",
    "in_stock": true,
    "per_page": 20
  }
}

# Response
{
  "products": [
    {
      "product_id": 101,
      "name": "Premium Widget",
      "sku": "PREM-WIDGET-001",
      "price": "49.99",
      "regular_price": "59.99",
      "sale_price": "49.99",
      "stock_status": "instock",
      "categories": ["widgets", "premium"]
    }
  ]
}
```

## Example 6: Get Product by SKU

```python
# MCP Tool Invocation
{
  "name": "get_product",
  "arguments": {
    "sku": "PREM-WIDGET-001"
  }
}
```

## Example 7: Create Customer

```python
# MCP Tool Invocation
{
  "name": "create_customer",
  "arguments": {
    "email": "john.doe@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "billing": {
      "first_name": "John",
      "last_name": "Doe",
      "address_1": "789 Pine St",
      "city": "San Francisco",
      "state": "CA",
      "postcode": "94102",
      "country": "US",
      "email": "john.doe@example.com",
      "phone": "555-987-6543"
    }
  }
}

# Response
{
  "customer_id": 68,
  "email": "john.doe@example.com",
  "username": "john.doe",
  "role": "customer",
  "created_at": "2024-03-31T20:35:00Z"
}
```

## Example 8: Get Customer

```python
# MCP Tool Invocation
{
  "name": "get_customer",
  "arguments": {
    "email": "john.doe@example.com"
  }
}

# Response
{
  "customer_id": 68,
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "billing": {...},
  "orders_count": 3,
  "total_spent": "299.97"
}
```

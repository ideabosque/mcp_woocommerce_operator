# WooCommerce API Reference

## Authentication

WooCommerce REST API uses OAuth 1.0a or Basic Authentication depending on your setup.

### Basic Auth (HTTPS)
```
Authorization: Basic {base64(consumer_key:consumer_secret)}
```

### Query String Auth (HTTP or HTTPS with specific configurations)
```
/wp-json/wc/v3/orders?consumer_key=ck_xxx&consumer_secret=cs_xxx
```

## Core Endpoints

### Orders

#### List Orders
```
GET /wp-json/wc/v3/orders
```
**Parameters:**
- `status` - pending, processing, completed, cancelled, refunded, failed, trash
- `customer` - Customer ID
- `date_created_min` - Minimum date created (ISO 8601)
- `date_created_max` - Maximum date created (ISO 8601)
- `page` - Current page
- `per_page` - Items per page (1-100)
- `orderby` - date, id, include, title, slug, price, popularity, rating
- `order` - asc, desc

#### Get Order
```
GET /wp-json/wc/v3/orders/{id}
```

#### Create Order
```
POST /wp-json/wc/v3/orders
```
**Request Body:**
```json
{
  "payment_method": "bacs",
  "payment_method_title": "Direct Bank Transfer",
  "set_paid": true,
  "billing": {
    "first_name": "John",
    "last_name": "Doe",
    "address_1": "969 Market",
    "address_2": "",
    "city": "San Francisco",
    "state": "CA",
    "postcode": "94103",
    "country": "US",
    "email": "john.doe@example.com",
    "phone": "(555) 555-5555"
  },
  "shipping": {
    "first_name": "John",
    "last_name": "Doe",
    "address_1": "969 Market",
    "address_2": "",
    "city": "San Francisco",
    "state": "CA",
    "postcode": "94103",
    "country": "US"
  },
  "line_items": [
    {
      "product_id": 93,
      "quantity": 2
    }
  ],
  "shipping_lines": [
    {
      "method_id": "flat_rate",
      "method_title": "Flat Rate",
      "total": "10.00"
    }
  ]
}
```

#### Update Order
```
PUT /wp-json/wc/v3/orders/{id}
```

#### Delete Order
```
DELETE /wp-json/wc/v3/orders/{id}
```

### Products

#### List Products
```
GET /wp-json/wc/v3/products
```

#### Get Product
```
GET /wp-json/wc/v3/products/{id}
```

#### Create Product
```
POST /wp-json/wc/v3/products
```

### Customers

#### List Customers
```
GET /wp-json/wc/v3/customers
```

#### Get Customer
```
GET /wp-json/wc/v3/customers/{id}
```

#### Create Customer
```
POST /wp-json/wc/v3/customers
```

## Response Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request
- `401 Unauthorized` - Authentication failed
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Rate Limiting

Default rate limits vary by hosting. Common limits:
- 100 requests per minute for GET
- 25 requests per minute for POST/PUT/DELETE

## Error Response Format

```json
{
  "code": "woocommerce_rest_{error_code}",
  "message": "Error description",
  "data": {
    "status": 400
  }
}
```

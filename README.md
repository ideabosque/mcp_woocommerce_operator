# MCP WooCommerce Operator

An MCP (Model Context Protocol) module that enables AI agents to interact with WooCommerce stores through a standardized interface.

## Features

- **Order Management**: List, retrieve, create, and update orders
- **Product Catalog**: Search and retrieve product information
- **Customer Management**: Create and retrieve customer profiles
- **Full MCP Compliance**: Implements standard MCP tools interface

## Installation

```bash
# Install with Poetry
poetry add mcp-woocommerce-operator

# Or with pip
pip install mcp-woocommerce-operator
```

## Configuration

### Required Settings

```python
{
    "woocommerce_url": "https://your-store.com",
    "consumer_key": "ck_your_consumer_key",
    "consumer_secret": "cs_your_consumer_secret",
    "api_version": "wc/v3",  # Optional, defaults to wc/v3
    "verify_ssl": True,       # Optional, defaults to True
    "timeout": 30,            # Optional, defaults to 30 seconds
    "query_string_auth": False,  # Optional, use for HTTP
}
```

### Environment Variables

Create a `.env` file (see `.env.example`):

```bash
WOOCOMMERCE_URL=https://your-store.com
WOOCOMMERCE_CONSUMER_KEY=ck_your_consumer_key
WOOCOMMERCE_CONSUMER_SECRET=cs_your_consumer_secret
```

## Available Tools

### Orders

1. **list_orders** - Retrieve orders with filtering options
2. **get_order** - Get detailed order information
3. **create_order** - Create a new order
4. **update_order_status** - Update order status

### Products

5. **list_products** - Search and list products
6. **get_product** - Get product details by ID or SKU

### Customers

7. **create_customer** - Create a new customer account
8. **get_customer** - Get customer information

## Usage Example

```python
from mcp_woocommerce_operator import MCPWooCommerceOperator
import logging

# Initialize logger
logger = logging.getLogger(__name__)

# Create operator instance
operator = MCPWooCommerceOperator(
    logger=logger,
    woocommerce_url="https://your-store.com",
    consumer_key="ck_your_key",
    consumer_secret="cs_your_secret",
)

# List recent orders
orders = operator.list_orders(
    status="processing",
    per_page=10
)

# Get specific order
order = operator.get_order(order_id=123)

# Create a new order
new_order = operator.create_order(
    customer_email="customer@example.com",
    customer_first_name="John",
    customer_last_name="Doe",
    line_items=[
        {"product_id": 101, "quantity": 2},
        {"product_id": 102, "quantity": 1},
    ],
    billing_address={
        "first_name": "John",
        "last_name": "Doe",
        "address_1": "123 Main St",
        "city": "New York",
        "state": "NY",
        "postcode": "10001",
        "country": "US",
        "email": "customer@example.com",
        "phone": "555-123-4567",
    }
)

# Update order status
operator.update_order_status(
    order_id=456,
    status="completed",
    note="Payment received"
)

# Search products
products = operator.list_products(
    search="widget",
    in_stock=True,
    min_price=10.0,
    max_price=100.0
)

# Get product by ID
product = operator.get_product(product_id=123)

# Get product by SKU
product = operator.get_product(sku="WIDGET-001")

# Create customer
customer = operator.create_customer(
    email="new@example.com",
    first_name="Jane",
    last_name="Smith",
    billing={
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "new@example.com",
    }
)

# Get customer
# By ID
customer = operator.get_customer(customer_id=789)
# By email
customer = operator.get_customer(email="customer@example.com")
```

## MCP Configuration

For MCP integration, use the following configuration:

```python
from mcp_woocommerce_operator import MCP_CONFIGURATION

# Configuration is ready to use with MCP server
config = MCP_CONFIGURATION
```

## API Reference

See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for detailed WooCommerce REST API documentation.

## Examples

See [docs/EXAMPLES.md](docs/EXAMPLES.md) for comprehensive usage examples.

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/ideabosque/mcp_woocommerce_operator.git
cd mcp_woocommerce_operator

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_woocommerce_operator --cov-report=html

# Run specific test file
pytest tests/test_woocommerce_client.py
```

### Code Quality

```bash
# Format with Black
black mcp_woocommerce_operator/ tests/

# Type checking
mypy mcp_woocommerce_operator/

# Linting
flake8 mcp_woocommerce_operator/ tests/
```

## Authentication

This module uses WooCommerce REST API authentication:

- **Basic Auth** (recommended for HTTPS)
- **Query String Auth** (for HTTP or specific configurations)

### Generating API Keys

1. Go to WooCommerce → Settings → Advanced → REST API
2. Click "Add key"
3. Set description and permissions
4. Generate and copy consumer key and secret

## Error Handling

The module provides detailed error messages for:

- Invalid credentials
- Connection failures
- WooCommerce API errors
- Validation errors
- Rate limiting

## WooCommerce API Compatibility

- **WooCommerce**: 3.5+
- **WordPress**: 4.4+
- **API Version**: wc/v3 (default)

## Security Considerations

- Store credentials in environment variables
- Use HTTPS for production stores
- Implement rate limiting for high-volume operations
- Validate all user inputs
- Sanitize data in logs

## License

MIT License - see [LICENSE](LICENSE) file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## Support

For issues and questions:
- GitHub Issues: https://github.com/ideabosque/mcp_woocommerce_operator/issues
- Documentation: See `docs/` folder

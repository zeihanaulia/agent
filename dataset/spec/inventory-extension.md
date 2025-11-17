# Inventory & Stock Tracking Feature Request

## Problem Statement
We need to track inventory levels for each product, including stock quantity, reorder point, and last restocked date. This is critical for inventory management and preventing stockouts.

## Requirements

### Core Features
1. **Stock Tracking**
   - Add `stockQuantity` field to track current stock level
   - Add `reorderPoint` field to define minimum stock threshold
   - Add `lastRestockedDate` to track when inventory was last updated
   - Add `warehouseLocation` to track physical storage location

2. **Inventory Management**
   - Create endpoint to update stock quantity
   - Create endpoint to check stock availability before purchase
   - Create endpoint to mark items as out of stock
   - Support batch stock updates

3. **Stock Alerts**
   - Notify when stock falls below reorder point
   - Track stock history for analytics
   - Generate low-stock reports

## Data Model

The Inventory feature should extend the Product entity with:
- `stock_quantity`: INT (non-null, default 0)
- `reorder_point`: INT (non-null, default 10)
- `last_restocked_date`: TIMESTAMP
- `warehouse_location`: VARCHAR(255)

## API Endpoints
- `PUT /api/products/{id}/stock` - Update stock quantity
- `GET /api/products/{id}/stock` - Check stock availability
- `GET /api/products/low-stock` - List items below reorder point

## Expected Implementation
- Modify the existing Product entity to include stock fields
- Add stock management methods to ProductService
- Create new ProductStockController for stock operations
- Extend ProductMapper to include stock information in responses
- Update ProductRequest/ProductResponse DTOs with stock fields

## Notes
- This is an extension of existing Product functionality
- No new domain entities needed
- Stock tracking is a cross-cutting concern for products
- Should maintain backward compatibility with existing product API

# INTEGRATION_CHECKLIST

## 사용자 웹

- [ ] GET /api/v1/products?featured=true
- [ ] GET /api/v1/products
- [ ] GET /api/v1/products/{product_id}
- [ ] GET /api/v1/products/{product_id}/slots
- [ ] POST /api/v1/auth/customers/signup
- [ ] POST /api/v1/auth/email/verify
- [ ] POST /api/v1/auth/login
- [ ] POST /api/v1/reservations/preview
- [ ] POST /api/v1/reservations
- [ ] POST /api/v1/orders/from-reservation
- [ ] POST /api/v1/payments/mock-approve
- [ ] GET /api/v1/me/orders
- [ ] GET /api/v1/me/orders/{order_id}
- [ ] GET /api/v1/me/orders/{order_id}/shipment
- [ ] POST /api/v1/returns
- [ ] GET /api/v1/me/returns

## 점주 앱

- [ ] POST /api/v1/auth/login
- [ ] GET /api/v1/owner/dashboard
- [ ] GET /api/v1/owner/farms/me
- [ ] PUT /api/v1/owner/farms/{farm_id}
- [ ] GET /api/v1/owner/products
- [ ] POST /api/v1/owner/products
- [ ] PUT /api/v1/owner/products/{product_id}
- [ ] PATCH /api/v1/owner/products/{product_id}/status
- [ ] POST /api/v1/owner/ml/predictions
- [ ] GET /api/v1/owner/ml/predictions
- [ ] POST /api/v1/owner/harvest-slots
- [ ] GET /api/v1/owner/harvest-slots
- [ ] GET /api/v1/owner/reservations
- [ ] GET /api/v1/owner/orders
- [ ] GET /api/v1/owner/procurements
- [ ] GET /api/v1/owner/procurements/{procurement_id}
- [ ] PATCH /api/v1/owner/procurements/{procurement_id}/decision
- [ ] POST /api/v1/owner/quality-inspections
- [ ] GET /api/v1/owner/quality-inspections
- [ ] POST /api/v1/owner/shipments
- [ ] PATCH /api/v1/owner/shipments/{shipment_id}/status
- [ ] GET /api/v1/owner/returns
- [ ] PATCH /api/v1/owner/returns/{return_request_id}/decision
- [ ] GET /api/v1/owner/profile
- [ ] PUT /api/v1/owner/profile

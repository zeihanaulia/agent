# 🚚 Smart Delivery Routing System — Full Specification

## 🎯 Feature Request

Build a **real-time delivery routing and optimization system** for a fleet of couriers delivering packages across cities.
The system must assign deliveries, optimize routes using live traffic data, track courier positions, and notify customers when delivery status changes.

---

## 🧠 Overview

This service will coordinate **couriers, deliveries, vehicles, and routes** with smart route planning and progress tracking.
It combines geolocation APIs, ETA predictions, and business logic for delivery prioritization (e.g., express > normal).

---

## 🧰 Tech Stack

| Component     | Tech                                        |
| ------------- | ------------------------------------------- |
| Language      | Java 17                                     |
| Framework     | Spring Boot 3.x                             |
| DB            | PostgreSQL + PostGIS (for geospatial data)  |
| Message Queue | Kafka (for live location stream)            |
| External      | OpenRouteService / Google Maps API          |
| Build         | Maven                                       |
| Auth          | JWT + Role-based (Admin, Courier, Customer) |

---

## 🧩 Core Entities

* **Courier** — drivers responsible for deliveries
* **Vehicle** — registered vehicles with capacity and type
* **PackageDelivery** — a delivery job (pickup → drop-off)
* **RoutePlan** — optimized route assigned to a courier
* **GeoPoint** — lat/lon tracking data
* **NotificationEvent** — status updates to customers

---

## 🚏 API Endpoints

### 👤 Courier Management

```
POST   /api/couriers                      - Register new courier
GET    /api/couriers                      - List all couriers
GET    /api/couriers/{id}                 - Get courier detail
PUT    /api/couriers/{id}                 - Update courier info
GET    /api/couriers/available            - Get couriers currently idle
PATCH  /api/couriers/{id}/status          - Update availability/status
GET    /api/couriers/{id}/location        - Current GPS location
```

### 🚗 Vehicle Management

```
POST   /api/vehicles                      - Register new vehicle
GET    /api/vehicles                      - List all vehicles
GET    /api/vehicles/{id}                 - Get vehicle detail
PUT    /api/vehicles/{id}                 - Update vehicle info
GET    /api/vehicles/assigned/{courierId} - Get vehicle by courier
```

### 📦 Package Deliveries

```
POST   /api/deliveries                    - Create delivery job
GET    /api/deliveries                    - List all deliveries
GET    /api/deliveries/{id}               - Get delivery detail
PUT    /api/deliveries/{id}/assign        - Assign courier & vehicle
PUT    /api/deliveries/{id}/status        - Update delivery status (PICKED_UP, IN_TRANSIT, DELIVERED)
GET    /api/deliveries/customer/{id}      - Get all deliveries for a customer
GET    /api/deliveries/active             - List ongoing deliveries
DELETE /api/deliveries/{id}               - Cancel delivery
```

### 🧭 Route Planning & Optimization

```
POST   /api/routes/plan                   - Generate optimized route for courier (multi-stop)
GET    /api/routes/{id}                   - Get route details
POST   /api/routes/recalculate            - Recalculate route due to traffic/delay
GET    /api/routes/courier/{id}/active    - Get courier’s active route
GET    /api/routes/history/{courierId}    - Route history
```

### 🛰️ Live Location Tracking

```
POST   /api/locations/update              - Update courier location (Kafka stream)
GET    /api/locations/courier/{id}        - Get latest location
GET    /api/locations/delivery/{id}       - Trace full route for one delivery
```

### 🔔 Notifications & Events

```
POST   /api/notifications                 - Create customer notification
GET    /api/notifications/customer/{id}   - List all notifications for a customer
GET    /api/notifications/unread          - Get unread notifications
PATCH  /api/notifications/{id}/read       - Mark as read
```

### 🧮 Reports & Analytics

```
GET    /api/reports/delivery-time         - Avg delivery time by region
GET    /api/reports/fleet-utilization     - Fleet usage summary
GET    /api/reports/top-couriers          - Top couriers by delivery volume
GET    /api/reports/delivery-failures     - Failed/canceled deliveries
```

---

## ⚙️ Business Logic

### Route Planning

* Optimize courier route using OpenRouteService API
* Respect vehicle capacity limits
* Factor traffic delays and delivery priorities
* Dynamic re-routing when ETA changes > 15%

### Delivery Assignment

* Idle courier nearest to pickup location
* Weighted scoring: distance + active load + rating
* Fallback to standby pool if all busy

### Notifications

* Trigger on state transitions:

  * `CREATED → ASSIGNED` → "Courier found"
  * `PICKED_UP` → "Package picked up"
  * `DELIVERED` → "Delivered successfully"

### Tracking

* Kafka topic: `courier-location`
* Real-time dashboard via WebSocket: `/ws/location-stream`

---

## 🧱 Entity Relationships

| Entity                              | Relation                     | Type |
| ----------------------------------- | ---------------------------- | ---- |
| Courier → Vehicle                   | 1-to-1                       |      |
| Courier → RoutePlan                 | 1-to-many                    |      |
| RoutePlan → PackageDelivery         | 1-to-many                    |      |
| PackageDelivery → NotificationEvent | 1-to-many                    |      |
| Courier → GeoPoint                  | 1-to-many (location history) |      |

---

## 🧾 Example DTOs

```java
public record DeliveryRequest(
  String pickupAddress,
  String dropoffAddress,
  double pickupLat,
  double pickupLon,
  double dropoffLat,
  double dropoffLon,
  String priority,
  Long customerId
) {}
```

```java
public record RoutePlanResponse(
  Long courierId,
  List<DeliveryPoint> stops,
  double totalDistanceKm,
  double estimatedDurationMin
) {}
```

---

## 📊 Example Route Optimization Flow

1. User creates 5 pending deliveries.
2. System fetches all coordinates → builds route graph.
3. Sends request to OpenRouteService.
4. Saves optimized route → `RoutePlan`.
5. Pushes result to courier mobile app via WebSocket.

---

## 🧪 Testing Strategy

* Unit: route scoring algorithm, ETA calculator
* Integration: route generation API calls
* Kafka: location stream → DB listener validation
* E2E: simulate multi-courier delivery session

---

## 🧩 Deployment & Scaling

* `@Async` route computation workers
* Kafka consumer group for `location-updates`
* Cache route results in Redis for fast ETA lookup
* Use Docker + Traefik for routing across microservices
* `/actuator/metrics` for fleet performance

---

## ✅ Success Criteria

* End-to-end delivery simulation works for ≥ 10 couriers
* Route optimization latency < 2s
* Kafka consumer handles >1000 updates/min
* 95% of deliveries complete under ETA margin
* Pass load test: 100 concurrent route generations

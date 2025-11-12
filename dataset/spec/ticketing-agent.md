# 🎫 Smart Event Ticketing & Recommendation System

## 🎯 Use Case Overview

Sebuah platform yang memungkinkan user untuk:

* Menemukan event sesuai minatnya (AI-driven recommendation).
* Membeli tiket dan mendapatkan QR-code untuk masuk.
* Menyimpan tiket dalam wallet digital.
* Menilai event setelah hadir (feedback & rating).
* Melihat rekomendasi berdasarkan preferensi dan riwayat transaksi.

---

## 🧠 Business Requirements

1. **User Flow**

   * User register/login.
   * Browse event berdasarkan kategori, lokasi, atau tanggal.
   * Lihat rekomendasi berdasarkan preferensi dan histori pembelian.
   * Pesan tiket dan bayar (mock payment gateway).
   * Dapatkan QR code untuk validasi di gate.
   * Setelah event selesai, beri rating.

2. **Organizer Flow**

   * CRUD event.
   * Upload poster dan detail event.
   * Monitor jumlah tiket terjual.
   * Lihat review dan rating event.

3. **Admin Flow**

   * CRUD kategori event.
   * Approve event yang diajukan organizer.
   * Melihat laporan transaksi harian/bulanan.

---

## 🧰 Tech Stack

| Layer          | Tech                               |
| -------------- | ---------------------------------- |
| Backend        | Spring Boot 3.3 (Java 17)          |
| DB             | PostgreSQL                         |
| Storage        | AWS S3 (untuk poster upload)       |
| Auth           | JWT                                |
| Recommendation | Collaborative filtering (simulasi) |
| Payment        | Mock via Midtrans sandbox API      |

---

## 🧩 Entities

| Entity      | Description                             |
| ----------- | --------------------------------------- |
| User        | Registered user (customer or organizer) |
| Event       | Detail acara dan tiket yang tersedia    |
| Ticket      | Tiket yang dibeli user                  |
| Transaction | Data pembelian (payment + ticket info)  |
| Review      | Feedback dan rating setelah event       |
| Category    | Jenis event (music, sport, tech, dll.)  |

---

## 🚏 API Endpoints (with Request/Response)

---

### 👤 User Management

#### **POST /api/users/register**

**Request**

```json
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "securePass123",
  "role": "CUSTOMER"
}
```

**Response**

```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "role": "CUSTOMER",
  "createdAt": "2025-11-12T10:30:00Z"
}
```

---

#### **POST /api/auth/login**

**Request**

```json
{
  "email": "john@example.com",
  "password": "securePass123"
}
```

**Response**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600
}
```

---

### 🎟️ Event Management

#### **POST /api/events**

**Role:** Organizer only
**Request**

```json
{
  "title": "Java Developer Summit 2025",
  "categoryId": 3,
  "location": "Jakarta Convention Center",
  "date": "2025-12-02T09:00:00Z",
  "price": 250000,
  "capacity": 500,
  "posterUrl": "https://cdn.simplify.ai/events/jds2025.png",
  "description": "The biggest Java tech event in Indonesia!"
}
```

**Response**

```json
{
  "id": 102,
  "title": "Java Developer Summit 2025",
  "status": "PENDING_APPROVAL",
  "createdBy": {
    "id": 7,
    "name": "OrganizerX"
  }
}
```

---

#### **GET /api/events**

**Query params:**
`categoryId`, `city`, `date`, `keyword`

**Response**

```json
[
  {
    "id": 101,
    "title": "Coldplay Live in Jakarta",
    "category": "Music",
    "date": "2025-11-20T19:00:00Z",
    "location": "GBK Stadium",
    "price": 1200000,
    "availableSeats": 300
  },
  {
    "id": 102,
    "title": "Java Developer Summit 2025",
    "category": "Tech",
    "price": 250000,
    "availableSeats": 500
  }
]
```

---

### 💳 Ticket Purchase

#### **POST /api/tickets/purchase**

**Request**

```json
{
  "eventId": 102,
  "userId": 1,
  "quantity": 2,
  "paymentMethod": "CREDIT_CARD"
}
```

**Response**

```json
{
  "transactionId": "TRX-20251112-0001",
  "eventTitle": "Java Developer Summit 2025",
  "totalAmount": 500000,
  "status": "PAID",
  "tickets": [
    {
      "ticketId": "TCK-20251112-ABC123",
      "qrCodeUrl": "https://cdn.simplify.ai/qr/TCK-20251112-ABC123.png"
    },
    {
      "ticketId": "TCK-20251112-ABC124",
      "qrCodeUrl": "https://cdn.simplify.ai/qr/TCK-20251112-ABC124.png"
    }
  ]
}
```

---

### 📊 Recommendation System

#### **GET /api/recommendations/{userId}**

**Response**

```json
{
  "userId": 1,
  "recommendations": [
    {
      "eventId": 105,
      "title": "Google Cloud Summit 2025",
      "category": "Tech",
      "reason": "You attended 'Java Developer Summit 2025'"
    },
    {
      "eventId": 204,
      "title": "Coldplay Live in Jakarta",
      "category": "Music",
      "reason": "Popular among similar users"
    }
  ]
}
```

---

### 🌟 Review System

#### **POST /api/reviews**

**Request**

```json
{
  "eventId": 102,
  "userId": 1,
  "rating": 5,
  "comment": "Fantastic speakers and great networking!"
}
```

**Response**

```json
{
  "id": 501,
  "eventId": 102,
  "user": { "id": 1, "name": "John Doe" },
  "rating": 5,
  "comment": "Fantastic speakers and great networking!",
  "createdAt": "2025-11-12T11:00:00Z"
}
```

---

### 🏦 Admin: Approve Event

#### **PUT /api/admin/events/{eventId}/approve**

**Response**

```json
{
  "id": 102,
  "title": "Java Developer Summit 2025",
  "status": "APPROVED",
  "approvedAt": "2025-11-13T09:00:00Z"
}
```

---

### 🧾 Reports (Admin Only)

#### **GET /api/reports/sales?from=2025-11-01&to=2025-11-30**

**Response**

```json
{
  "totalRevenue": 75000000,
  "totalTicketsSold": 1420,
  "topEvents": [
    {
      "eventId": 101,
      "title": "Coldplay Live in Jakarta",
      "revenue": 40000000
    },
    {
      "eventId": 102,
      "title": "Java Developer Summit 2025",
      "revenue": 15000000
    }
  ]
}
```

---

## 📦 Database Schema (simplified)

```sql
TABLE users (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(100),
  email VARCHAR(100) UNIQUE,
  password_hash TEXT,
  role VARCHAR(20),
  created_at TIMESTAMP
);

TABLE events (
  id BIGSERIAL PRIMARY KEY,
  title VARCHAR(200),
  category_id BIGINT,
  location VARCHAR(200),
  date TIMESTAMP,
  price DECIMAL,
  capacity INT,
  status VARCHAR(20),
  created_by BIGINT REFERENCES users(id)
);

TABLE tickets (
  id BIGSERIAL PRIMARY KEY,
  event_id BIGINT REFERENCES events(id),
  user_id BIGINT REFERENCES users(id),
  qr_code_url TEXT,
  purchase_time TIMESTAMP
);

TABLE transactions (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT,
  event_id BIGINT,
  amount DECIMAL,
  payment_method VARCHAR(50),
  status VARCHAR(20),
  created_at TIMESTAMP
);

TABLE reviews (
  id BIGSERIAL PRIMARY KEY,
  event_id BIGINT REFERENCES events(id),
  user_id BIGINT REFERENCES users(id),
  rating INT,
  comment TEXT,
  created_at TIMESTAMP
);
```

---

## 🧩 Response Pattern

All responses follow this pattern:

```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2025-11-12T12:00:00Z"
}
```

or

```json
{
  "status": "error",
  "message": "Event not found",
  "timestamp": "2025-11-12T12:01:00Z"
}
```

---

## ✅ Success Metrics

| Metric                    | Target              |
| ------------------------- | ------------------- |
| Avg API latency           | < 250 ms            |
| Recommendation accuracy   | > 70% click-through |
| Ticket generation latency | < 1 sec             |
| Report generation         | < 3 sec             |
| Uptime                    | 99.9%               |

---



# Pompey Helper API

Base URL: `http://localhost:5000`

Authenticated endpoints require a Bearer token in the `Authorization` header:
```
Authorization: Bearer <token>
```

---

## Auth

### `POST /user/register`
Create a new account.

**Body**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Responses**
| Status | Body |
|--------|------|
| 200 | `{ "message": "User registered successfully" }` |
| 400 | Missing fields or username/email already taken |

---

### `POST /user/login`
Log in and receive a JWT token (valid 1 hour).

**Body**
```json
{
  "username": "string",
  "password": "string"
}
```

**Responses**
| Status | Body |
|--------|------|
| 200 | `{ "token": "string" }` |
| 400 | Missing fields |
| 401 | Invalid credentials |

---

### `GET /user/profile` 🔒
Get the authenticated user's profile.

**Responses**
| Status | Body |
|--------|------|
| 200 | `{ "username": "string", "email": "string", "waffle": integer }` |
| 401 | Missing or invalid token |
| 404 | User not found |

---

## Acts

### `GET /acts`
List all acts.

**Response `200`**
```json
[
  {
    "id": 1,
    "userId": 2,
    "location": "Southsea Common",
    "category": "Community",
    "item": "Pick up litter for 10 minutes",
    "claimedBy": 3,
    "completed": false
  }
]
```

---

### `POST /acts/register` 🔒
Post a new act. Costs **5 waffles**.

**Body**
```json
{
  "location": "string",
  "category": "string",
  "item": "string"
}
```

**Responses**
| Status | Body |
|--------|------|
| 201 | `{ "message": "Act registered successfully" }` |
| 400 | Missing fields |
| 402 | Insufficient waffles (need 5) |
| 401 | Missing or invalid token |

---

### `POST /acts/claim/<act_id>` 🔒
Claim an act to complete it.

**Responses**
| Status | Body |
|--------|------|
| 200 | `{ "message": "Act claimed successfully" }` |
| 400 | Cannot claim your own act |
| 401 | Missing or invalid token |
| 404 | Act not found |
| 409 | Already claimed or completed |

---

### `POST /acts/complete/<act_id>` 🔒
Mark a claimed act as complete. Earns **7 waffles**.

**Responses**
| Status | Body |
|--------|------|
| 200 | `{ "message": "Act marked as completed" }` |
| 401 | Missing or invalid token |
| 403 | Act not claimed by you |
| 404 | Act not found |
| 409 | Already completed |

---

## Merch

### `GET /merch`
List all merch items.

**Response `200`**
```json
[
  {
    "name": "Waffle Iron Tee",
    "waffles": 12,
    "provider": "GridLock Apparel",
    "img": "merch/waffle_iron_tee.jpg"
  }
]
```

---

### `POST /merch/register` 🔒
Add a new merch item.

**Body**
```json
{
  "name": "string",
  "waffles": integer,
  "provider": "string",
  "img": "merch/filename.jpg"
}
```

**Responses**
| Status | Body |
|--------|------|
| 201 | `{ "message": "Merch registered successfully" }` |
| 400 | Missing or invalid fields |
| 401 | Missing or invalid token |
| 409 | Item with that name already exists |

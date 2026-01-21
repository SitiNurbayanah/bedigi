# BeDigi API Documentation

Dokumentasi lengkap untuk EvalidaSign Digital Signature System API.

## 📋 Daftar Isi

- [Informasi Umum](#informasi-umum)
- [Authentication](#authentication)
- [File Management](#file-management)
- [Signatures](#signatures)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Testing Guide](#testing-guide)

---

## Informasi Umum

### Base URL
```
http://localhost:8000
```

### Authentication
Sebagian besar endpoint memerlukan JWT token yang didapat dari endpoint login. Token harus disertakan dalam header:

```http
Authorization: Bearer <your_jwt_token>
```

### Content Type
Semua request dan response menggunakan JSON kecuali untuk upload file yang menggunakan `multipart/form-data`.

```http
Content-Type: application/json
```

### Response Format
Semua response mengikuti format standar:

**Success Response:**
```json
{
  "message": "Success message",
  "data": {...}
}
```

**Error Response:**
```json
{
  "error": "Error message"
}
```

---

## Authentication

### 1. Register User

Mendaftarkan user baru ke sistem.

**Endpoint:**
```http
POST /auth/register
```

**Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "nim_nip": "string",     // Required, unique identifier
  "name": "string",        // Required, nama lengkap user
  "password": "string",    // Required, min 6 karakter
  "role": "string"         // Required: mahasiswa|dosen|kajur|admin
}
```

**Example Request:**
```json
{
  "nim_nip": "MHS001",
  "name": "John Doe",
  "password": "password123",
  "role": "mahasiswa"
}
```

**Success Response (201 Created):**
```json
{
  "message": "Registrasi berhasil"
}
```

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 409 Conflict | `{"error": "User sudah terdaftar"}` | NIM/NIP sudah digunakan |
| 400 Bad Request | `{"error": "Data tidak lengkap"}` | Field wajib tidak lengkap |

---

### 2. Login

Autentikasi user dan mendapatkan JWT token.

**Endpoint:**
```http
POST /auth/login
```

**Rate Limit:** 5 requests per minute

**Headers:**
```http
Content-Type: application/json
```

**Request Body:**
```json
{
  "nim_nip": "string",     // Required
  "password": "string"     // Required
}
```

**Example Request:**
```json
{
  "nim_nip": "MHS001",
  "password": "password123"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Login berhasil",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "name": "John Doe",
  "role": "mahasiswa"
}
```

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 401 Unauthorized | `{"error": "Login gagal"}` | NIM/NIP atau password salah |
| 429 Too Many Requests | `{"error": "Rate limit exceeded"}` | Terlalu banyak percobaan login |

---

### 3. Logout

Logout user (dummy endpoint - token dihapus di client side).

**Endpoint:**
```http
POST /auth/logout
```

**Headers:**
```http
Content-Type: application/json
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "message": "Logout berhasil (client-side token deletion)"
}
```

---

### 4. Get Profile

Mendapatkan informasi profil user yang sedang login.

**Endpoint:**
```http
GET /auth/profile
```

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
{
  "nim_nip": "MHS001",
  "name": "John Doe",
  "role": "mahasiswa",
  "created_at": "2025-01-21 10:30:00"
}
```

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 404 Not Found | `{"error": "User tidak ditemukan"}` | User sudah dihapus dari sistem |
| 401 Unauthorized | `{"msg": "Missing Authorization Header"}` | Token tidak disertakan |

---

## File Management

### 1. Ajukan File

Mengajukan dokumen baru untuk ditandatangani.

**Endpoint:**
```http
POST /files/ajukan
```

**Authorization:** Required (Mahasiswa/Dosen)

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

**Request Body (form-data):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | File | ✓ | PDF file yang akan diajukan |
| filename | String | ✓ | Nama file (tanpa ekstensi) |
| jenis_file | String | ✓ | Jenis dokumen (e.g., "Surat Keterangan") |
| signer_nim | String[] | ✓ | Array NIM/NIP penandatangan |
| urutan_signer | Integer[] | ✓ | Array urutan penandatanganan |

**Example (Postman):**

```
KEY              | VALUE                  | TYPE
-----------------|------------------------|--------
file             | [choose file]          | File
filename         | Surat Tugas Akhir      | Text
jenis_file       | Surat Keterangan       | Text
signer_nim       | DOSEN001               | Text
signer_nim       | DOSEN002               | Text
signer_nim       | KAJUR001               | Text
urutan_signer    | 1                      | Text
urutan_signer    | 2                      | Text
urutan_signer    | 3                      | Text
```

**Cara Menambahkan Tag di PDF:**

Sebelum upload, tambahkan tag `#1`, `#2`, `#3`, dst. di posisi mana Anda ingin nama penandatangan muncul. Tag akan diganti dengan nama dan NIM/NIP signer sesuai urutan.

**Success Response (201 Created):**
```json
{
  "message": "File berhasil diajukan",
  "unique_code": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 400 Bad Request | `{"error": "Data tidak lengkap"}` | Field wajib tidak lengkap |
| 404 Not Found | `{"error": "User tidak ditemukan"}` | User pengaju tidak valid |

---

### 2. View File

Download file PDF (sebelum atau sesudah ditandatangani).

**Endpoint:**
```http
GET /files/view_file/<unique_code>
```

**Authorization:** Not required (public)

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| unique_code | String | Unique code dari file |

**Example:**
```http
GET /files/view_file/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Success Response (200 OK):**
- File PDF untuk di-download
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="<filename>.pdf"`

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 404 Not Found | `{"error": "File tidak ditemukan"}` | Unique code tidak valid |

---

### 3. File Detail

Mendapatkan detail informasi file dan status penandatanganan.

**Endpoint:**
```http
GET /files/file_detail/<unique_code>
```

**Authorization:** Not required (public)

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| unique_code | String | Unique code dari file |

**Example:**
```http
GET /files/file_detail/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Success Response (200 OK):**
```json
{
  "filename": "Surat Tugas Akhir",
  "jenis_file": "Surat Keterangan",
  "tanggal_diajukan": "2025-01-21 10:30:00",
  "global_status": "Menunggu TTD Dosen",
  "pengaju": "John Doe",
  "role_pengaju": "mahasiswa",
  "signers": [
    {
      "name": "Dr. Jane Smith",
      "nim_nip": "DOSEN001",
      "role": "dosen",
      "sign_status": "menunggu dosen",
      "status_icon": "❌"
    },
    {
      "name": "Dr. Bob Johnson",
      "nim_nip": "DOSEN002",
      "role": "dosen",
      "sign_status": "signed",
      "status_icon": "✅"
    },
    {
      "name": "Prof. Alice Williams",
      "nim_nip": "KAJUR001",
      "role": "kajur",
      "sign_status": "menunggu dosen",
      "status_icon": "❌"
    }
  ]
}
```

**Global Status Values:**
- `Menunggu TTD Dosen` - Menunggu tanda tangan dosen
- `Diajukan ke Ketua Jurusan` - Semua dosen sudah sign, menunggu kajur
- `Completed` - Semua sudah menandatangani

**Sign Status Values:**
- `menunggu dosen` - Belum bisa ditandatangani (menunggu giliran)
- `menunggu kajur` - Siap ditandatangani oleh kajur
- `signed` - Sudah ditandatangani (dosen)
- `completed` - Sudah ditandatangani (kajur)

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 404 Not Found | `{"error": "File tidak ditemukan"}` | Unique code tidak valid |

---

### 4. Mahasiswa Preview

Melihat daftar file yang diajukan oleh mahasiswa yang sedang login.

**Endpoint:**
```http
GET /files/mhs_preview
```

**Authorization:** Required (Mahasiswa)

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
[
  {
    "filename": "Surat Tugas Akhir",
    "jenis_file": "Surat Keterangan",
    "tanggal_diajukan": "2025-01-21 10:30:00",
    "global_status": "Menunggu TTD Dosen",
    "unique_code": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  },
  {
    "filename": "Surat Penelitian",
    "jenis_file": "Surat Izin",
    "tanggal_diajukan": "2025-01-20 14:20:00",
    "global_status": "Completed",
    "unique_code": "b2c3d4e5-f6g7-8901-bcde-fg2345678901"
  }
]
```

---

### 5. Admin Preview

Melihat semua file dalam sistem (hanya untuk admin).

**Endpoint:**
```http
GET /files/admin_preview
```

**Authorization:** Required (Admin only)

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
[
  {
    "filename": "Surat Tugas Akhir",
    "jenis_file": "Surat Keterangan",
    "tanggal_diajukan": "2025-01-21 10:30:00",
    "global_status": "Menunggu TTD Dosen",
    "name": "John Doe",
    "role_pengaju": "mahasiswa"
  },
  {
    "filename": "Surat Penelitian",
    "jenis_file": "Surat Izin",
    "tanggal_diajukan": "2025-01-20 14:20:00",
    "global_status": "Completed",
    "name": "Jane Smith",
    "role_pengaju": "mahasiswa"
  }
]
```

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 403 Forbidden | `{"error": "Akses hanya untuk admin"}` | User bukan admin |

---

## Signatures

### 1. Dosen Preview

Melihat daftar file yang perlu ditandatangani oleh dosen.

**Endpoint:**
```http
GET /sign/dosen_preview
```

**Authorization:** Required (Dosen only)

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
[
  {
    "filename": "Surat Tugas Akhir",
    "jenis_file": "Surat Keterangan",
    "tanggal_diajukan": "2025-01-21 10:30:00",
    "global_status": "Menunggu TTD Dosen",
    "sign_status": "menunggu dosen",
    "unique_code": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "role_pengaju": "mahasiswa",
    "name": "John Doe"
  }
]
```

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 403 Forbidden | `{"error": "Akses hanya untuk dosen"}` | User bukan dosen |

---

### 2. Dosen Sign

Menandatangani file sebagai dosen.

**Endpoint:**
```http
POST /sign/dosen_sign/<unique_code>
```

**Authorization:** Required (Dosen only)

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| unique_code | String | Unique code dari file |

**Request Body:** (kosong atau `{}`)

**Example:**
```http
POST /sign/dosen_sign/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Success Response (200 OK):**
```json
{
  "message": "Berhasil tanda tangan sebagai dosen"
}
```

**Proses Otomatis:**
1. Status tanda tangan dosen diubah menjadi `signed`
2. Cek apakah masih ada dosen lain yang belum sign
3. Jika semua dosen sudah sign:
   - Update status kajur menjadi `menunggu kajur`
   - Update global_status menjadi `Diajukan ke Ketua Jurusan`
4. Jika tidak ada kajur dalam daftar signer:
   - Update global_status menjadi `Completed`
   - Generate final PDF dengan QR code

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 403 Forbidden | `{"error": "Akses hanya untuk dosen"}` | User bukan dosen |
| 403 Forbidden | `{"error": "Tidak dapat menandatangani file ini"}` | Status bukan "menunggu dosen" |
| 404 Not Found | `{"error": "File tidak ditemukan"}` | Unique code tidak valid |

---

### 3. Kajur Preview

Melihat daftar file yang siap ditandatangani oleh ketua jurusan.

**Endpoint:**
```http
GET /sign/kajur_preview
```

**Authorization:** Required (Kajur only)

**Headers:**
```http
Authorization: Bearer <access_token>
```

**Success Response (200 OK):**
```json
[
  {
    "filename": "Surat Tugas Akhir",
    "jenis_file": "Surat Keterangan",
    "tanggal_diajukan": "2025-01-21 10:30:00",
    "global_status": "Diajukan ke Ketua Jurusan",
    "unique_code": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "role_pengaju": "mahasiswa",
    "name": "John Doe"
  }
]
```

**Note:** Hanya menampilkan file yang semua dosennya sudah menandatangani.

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 403 Forbidden | `{"error": "Akses hanya untuk ketua jurusan"}` | User bukan kajur |

---

### 4. Kajur Sign

Menandatangani file sebagai ketua jurusan (final approval).

**Endpoint:**
```http
POST /sign/kajur_sign/<unique_code>
```

**Authorization:** Required (Kajur only)

**Headers:**
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| unique_code | String | Unique code dari file |

**Request Body:** (kosong atau `{}`)

**Example:**
```http
POST /sign/kajur_sign/a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

**Success Response (200 OK):**
```json
{
  "message": "Berhasil tanda tangan sebagai kajur"
}
```

**Proses Otomatis:**
1. Validasi semua dosen sudah menandatangani
2. Update status kajur menjadi `completed`
3. Update global_status menjadi `Completed`
4. Generate final PDF dengan embedded QR code
5. Simpan ke `file_after_signed`

**Error Responses:**

| Status Code | Response | Keterangan |
|-------------|----------|------------|
| 403 Forbidden | `{"error": "Akses hanya untuk ketua jurusan"}` | User bukan kajur |
| 403 Forbidden | `{"error": "Tidak dapat menandatangani file ini"}` | Status bukan "menunggu kajur" |
| 403 Forbidden | `{"error": "Masih ada dosen yang belum tanda tangan..."}` | Ada dosen yang belum sign |
| 404 Not Found | `{"error": "File tidak ditemukan"}` | Unique code tidak valid |

---

## Error Handling

### Standard Error Codes

| Status Code | Meaning | When It Occurs |
|-------------|---------|----------------|
| 200 | OK | Request berhasil |
| 201 | Created | Resource berhasil dibuat |
| 400 | Bad Request | Request body tidak valid |
| 401 | Unauthorized | Token tidak valid/expired |
| 403 | Forbidden | User tidak memiliki akses |
| 404 | Not Found | Resource tidak ditemukan |
| 409 | Conflict | Data sudah ada (duplicate) |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "error": "Detailed error message"
}
```

### JWT Errors

| Error Message | Keterangan |
|---------------|------------|
| `Missing Authorization Header` | Header Authorization tidak ada |
| `Token has expired` | Token sudah kadaluarsa |
| `Invalid token` | Token tidak valid/rusak |
| `Signature verification failed` | Token signature tidak cocok |

---

## Rate Limiting

### Login Endpoint

```
Endpoint: POST /auth/login
Limit: 5 requests per minute per IP
```

Jika limit terlampaui, akan mendapat response:
```json
{
  "error": "429 Too Many Requests: 5 per 1 minute"
}
```

**Solusi:** Tunggu 1 menit sebelum mencoba lagi.

---

## Testing Guide

### 1. Setup Test Environment

**Install Postman atau cURL**

**Import Collection:**
- Download Postman collection dari `/docs/postman_collection.json`
- Import ke Postman

### 2. Testing Flow

#### Step 1: Register Users

```bash
# Register Mahasiswa
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "MHS001",
    "name": "John Doe",
    "password": "password123",
    "role": "mahasiswa"
  }'

# Register Dosen 1
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "DOSEN001",
    "name": "Dr. Jane Smith",
    "password": "password123",
    "role": "dosen"
  }'

# Register Dosen 2
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "DOSEN002",
    "name": "Dr. Bob Johnson",
    "password": "password123",
    "role": "dosen"
  }'

# Register Kajur
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "KAJUR001",
    "name": "Prof. Alice Williams",
    "password": "password123",
    "role": "kajur"
  }'

# Register Admin
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "ADMIN001",
    "name": "Admin System",
    "password": "password123",
    "role": "admin"
  }'
```

#### Step 2: Login sebagai Mahasiswa

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "MHS001",
    "password": "password123"
  }'
```

**Response:**
```json
{
  "message": "Login berhasil",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "name": "John Doe",
  "role": "mahasiswa"
}
```

**Simpan `access_token` untuk request selanjutnya**

#### Step 3: Ajukan File

Gunakan Postman dengan form-data:
- Set `Authorization: Bearer <token_mahasiswa>`
- Upload PDF file dengan tag #1, #2, #3
- Isi signer_nim: DOSEN001, DOSEN002, KAJUR001
- Isi urutan_signer: 1, 2, 3

#### Step 4: Login sebagai Dosen 1 & Sign

```bash
# Login Dosen 1
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "DOSEN001",
    "password": "password123"
  }'

# Preview files
curl -X GET http://localhost:8000/sign/dosen_preview \
  -H "Authorization: Bearer <token_dosen1>"

# Sign file
curl -X POST http://localhost:8000/sign/dosen_sign/<unique_code> \
  -H "Authorization: Bearer <token_dosen1>" \
  -H "Content-Type: application/json"
```

#### Step 5: Login sebagai Dosen 2 & Sign

```bash
# Login Dosen 2
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "DOSEN002",
    "password": "password123"
  }'

# Sign file
curl -X POST http://localhost:8000/sign/dosen_sign/<unique_code> \
  -H "Authorization: Bearer <token_dosen2>" \
  -H "Content-Type: application/json"
```

#### Step 6: Login sebagai Kajur & Sign

```bash
# Login Kajur
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "KAJUR001",
    "password": "password123"
  }'

# Preview files (harus muncul setelah semua dosen sign)
curl -X GET http://localhost:8000/sign/kajur_preview \
  -H "Authorization: Bearer <token_kajur>"

# Sign file (final approval)
curl -X POST http://localhost:8000/sign/kajur_sign/<unique_code> \
  -H "Authorization: Bearer <token_kajur>" \
  -H "Content-Type: application/json"
```

#### Step 7: Verify & Download

```bash
# Cek detail file
curl -X GET http://localhost:8000/files/file_detail/<unique_code>

# Download signed file
curl -X GET http://localhost:8000/files/view_file/<unique_code> \
  --output signed_document.pdf
```

### 3. Test Scenarios

#### Scenario 1: Happy Path
- Mahasiswa ajukan → Dosen 1 sign → Dosen 2 sign → Kajur sign → Completed ✅

#### Scenario 2: Kajur Sign Before Dosen
- Mahasiswa ajukan → Kajur coba sign → Error: "Masih ada dosen yang belum tanda tangan" ❌

#### Scenario 3: Wrong Role Access
- Mahasiswa coba akses `/sign/dosen_preview` → Error: "Akses hanya untuk dosen" ❌

#### Scenario 4: Expired Token
- Login → Tunggu token expired → Access endpoint → Error: "Token has expired" ❌

#### Scenario 5: Rate Limit
- Login 6x dalam 1 menit → Error: "Too Many Requests" ❌

---

## Best Practices

### 1. Token Management
- Simpan token di secure storage (localStorage/sessionStorage)
- Refresh token sebelum expired
- Clear token saat logout

### 2. File Upload
- Validasi file size (max 10MB recommended)
- Validasi file type (hanya PDF)
- Tambahkan tag #1, #2, #3 di posisi yang tepat

### 3. Error Handling
- Selalu handle error response
- Show user-friendly error message
- Log error untuk debugging

### 4. Performance
- Gunakan pagination untuk list endpoint (future improvement)
- Cache file preview di client side
- Compress large PDF before upload

---

## Changelog

### Version 1.0.0 (2025-01-21)
- Initial release
- Basic authentication & authorization
- File upload & management
- Hierarchical signing workflow
- QR code integration
- PDF watermarking


---

**Last Updated:** January 21, 2025  
**API Version:** 1.0.0

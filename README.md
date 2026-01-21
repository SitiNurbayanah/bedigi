# BeDigi - Digital Signature System

Sistem tanda tangan digital untuk dokumen akademik dengan alur persetujuan bertingkat (Dosen → Ketua Jurusan).

## 📋 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Teknologi](#-teknologi)
- [Arsitektur Sistem](#-arsitektur-sistem)
- [Instalasi](#-instalasi)
- [Konfigurasi](#-konfigurasi)
- [Penggunaan](#-penggunaan)
- [API Documentation](#-api-documentation)
- [Database Schema](#-database-schema)
- [Alur Kerja Sistem](#-alur-kerja-sistem)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)
- [Kontribusi](#-kontribusi)

## ✨ Fitur Utama

- **Multi-Role Authentication**: Mahasiswa, Dosen, Ketua Jurusan, dan Admin
- **Hierarchical Signing**: Sistem persetujuan bertingkat dengan urutan penandatangan yang fleksibel
- **QR Code Integration**: Setiap dokumen dilengkapi QR code untuk verifikasi autentikasi
- **PDF Watermarking**: Embedded watermark dengan informasi penandatangan
- **Smart Workflow**: Status tracking otomatis dengan notifikasi role-based
- **Secure API**: JWT-based authentication dengan rate limiting
- **File Management**: Preview dokumen sebelum dan sesudah ditandatangani

## 🛠 Teknologi

### Backend
- **Flask** - Web framework
- **Flask-JWT-Extended** - JWT authentication
- **Flask-Limiter** - Rate limiting
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database

### PDF Processing
- **PyPDF2** - PDF manipulation
- **PyMuPDF (fitz)** - PDF text extraction & annotation
- **ReportLab** - PDF generation
- **Pillow (PIL)** - Image processing
- **qrcode** - QR code generation

### Security
- **Werkzeug** - Password hashing
- **python-dotenv** - Environment variables

## 🏗 Arsitektur Sistem

```
bedigi/
├── app/
│   ├── __init__.py           # Application factory
│   ├── models.py             # Database models
│   ├── routes/
│   │   ├── auth.py           # Authentication endpoints
│   │   ├── files.py          # File management endpoints
│   │   └── signatures.py     # Signature endpoints
│   └── utils/
│       ├── qr.py             # QR code generation
│       └── pdf_sign.py       # PDF signing utilities
├── app.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── .env                     # Environment variables
├── seed_users.py            # User seeding script
└── seed_files.py            # File seeding script
```

## 🚀 Instalasi

1. **Clone repository**
```bash
git clone https://github.com/SitiNurbayanah/bedigi.git
cd bedigi
```

2. **Setup environment variables**
```bash
# Edit .env jika diperlukan
```

3. **Jalankan dengan Docker Compose**
```bash
docker-compose up -d
```

4. **Seed data (opsional)**
```bash
python seed_users.py
python seed_files.py
```

5. **Jalankan web**
```bash
python app.py
```

Aplikasi akan berjalan di `http://localhost:8000`

## 📖 Penggunaan

### Quick Start

1. **Register sebagai Mahasiswa**
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "MHS001",
    "name": "John Doe",
    "password": "password123",
    "role": "mahasiswa"
  }'
```

2. **Login**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "nim_nip": "MHS001",
    "password": "password123"
  }'
```

3. **Ajukan Dokumen** (menggunakan form-data di Postman atau tools sejenis)

4. **Dosen/Kajur Sign** (setelah login dengan role masing-masing)

### User Roles

| Role | Hak Akses |
|------|-----------|
| **mahasiswa** | Mengajukan dokumen, melihat status dokumen sendiri |
| **dosen** | Menandatangani dokumen yang ditugaskan |
| **kajur** | Menandatangani dokumen setelah semua dosen approve |
| **admin** | Melihat semua dokumen dalam sistem |

## 📚 API Documentation

Dokumentasi lengkap API tersedia di: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### Endpoint Overview

#### Authentication
- `POST /auth/register` - Register user baru
- `POST /auth/login` - Login dan dapatkan JWT token
- `POST /auth/logout` - Logout (client-side)
- `GET /auth/profile` - Lihat profil user

#### File Management
- `POST /files/ajukan` - Ajukan dokumen baru
- `GET /files/view_file/<code>` - Download dokumen
- `GET /files/file_detail/<code>` - Detail dokumen & status
- `GET /files/mhs_preview` - List dokumen mahasiswa
- `GET /files/admin_preview` - List semua dokumen (admin only)

#### Signatures
- `GET /sign/dosen_preview` - List dokumen untuk dosen
- `POST /sign/dosen_sign/<code>` - Tanda tangan sebagai dosen
- `GET /sign/kajur_preview` - List dokumen untuk kajur
- `POST /sign/kajur_sign/<code>` - Tanda tangan sebagai kajur

## 🗄 Database Schema

### Users Table
```sql
CREATE TABLE Users (
    nim_nip VARCHAR(20) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(250) NOT NULL,
    role VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Files Table
```sql
CREATE TABLE Files (
    id_file SERIAL PRIMARY KEY,
    pengaju_nim VARCHAR(20) REFERENCES Users(nim_nip),
    filename VARCHAR(100) NOT NULL,
    jenis_file VARCHAR(50) NOT NULL,
    tanggal_diajukan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_before_signed BYTEA NOT NULL,
    file_after_signed BYTEA,
    global_status VARCHAR(100) DEFAULT 'Menunggu TTD Dosen',
    unique_code VARCHAR(100) UNIQUE NOT NULL,
    qr_code BYTEA
);
```

### FileSigns Table
```sql
CREATE TABLE FileSigns (
    id_filesigner SERIAL PRIMARY KEY,
    id_file INTEGER REFERENCES Files(id_file),
    signer_nim VARCHAR(20) REFERENCES Users(nim_nip),
    sign_status VARCHAR(50) DEFAULT 'menunggu dosen',
    urutan_signer INTEGER NOT NULL
);
```

## 🔄 Alur Kerja Sistem

### 1. Pengajuan Dokumen
```
Mahasiswa → Upload PDF + Pilih Signer → Sistem Generate QR Code
→ Embed Watermark → Status: "Menunggu TTD Dosen"
```

### 2. Tanda Tangan Dosen
```
Dosen Login → Lihat Dokumen Pending → Sign → 
Cek semua dosen sudah sign? 
├─ Ya → Update status kajur: "menunggu kajur"
└─ Tidak → Tunggu dosen lain
```

### 3. Tanda Tangan Kajur
```
Kajur Login → Lihat Dokumen Ready → 
Validasi semua dosen sudah sign → Sign → 
Generate Final PDF → Status: "Completed"
```

### Status Flow Diagram
```
┌─────────────────────┐
│  Menunggu TTD Dosen │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Dosen Sign (1,2,..)│
└──────────┬──────────┘
           │
           ▼
     ┌────┴────┐
     │All Dosen│
     │Signed?  │
     └────┬────┘
          │ Yes
          ▼
┌─────────────────────┐
│ Diajukan ke Kajur   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Kajur Sign        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Completed ✓      │
└─────────────────────┘
```

### Manual Testing dengan Postman

1. Import Postman Collection (tersedia di `/docs/postman_collection.json`)
2. Setup environment variables di Postman:
   - `base_url`: http://localhost:8000
   - `token`: (di-set setelah login)
3. Jalankan test scenario sesuai dokumentasi

### Sample Test Users
```python
# Jalankan seed_users.py untuk membuat user testing
python seed_users.py
```

User default:
- Mahasiswa: `2023001` / `12345`
- Dosen 1: `1988001` / `dosen123`
- Dosen 2: `1988002` / `dosen123`
- Kajur: `1977001` / `kajur123`
- Admin: `admin001` / `admin123`

## 🐛 Troubleshooting

### Database Connection Error
```
Error: Could not connect to database
```
**Solusi:**
1. Pastikan PostgreSQL sudah running
2. Cek credentials di `.env`
3. Buat database jika belum ada: `CREATE DATABASE bedigi_db;`

### JWT Token Expired
```
Error: Token has expired
```
**Solusi:**
Login ulang untuk mendapatkan token baru

### QR Code Generation Failed
```
Error: QR code image is not valid
```
**Solusi:**
1. Install ulang dependency: `pip install qrcode[pil]`
2. Pastikan library PIL/Pillow terinstall dengan benar

### PDF Processing Error
```
Error: Cannot merge PDF pages
```
**Solusi:**
1. Pastikan PDF input valid dan tidak corrupt
2. Cek apakah PyMuPDF terinstall: `pip install PyMuPDF`

### Rate Limit Exceeded
```
Error: 429 Too Many Requests
```
**Solusi:**
Tunggu 1 menit sebelum mencoba login kembali (limit: 5 request/menit)

---

**Made with ❤️ for Digital Document Management**

# Proyek Pemantauan dan Kontrol Edge Computing pada Alat Pengering Biji Kopi Portable

Proyek ini merupakan tugas implementasi edge computing pada alat pengering biji kopi portable. Sistem ini dirancang untuk memantau dan mengontrol proses pengeringan biji kopi secara efisien dengan memanfaatkan teknologi Internet of Things (IoT) dan Edge Computing. Data sensor seperti suhu dan kelembapan dikumpulkan secara real-time dari alat pengering, diproses pada edge node (Raspberry Pi), dan dikirimkan ke backend untuk visualisasi serta penyimpanan. Sistem juga memungkinkan kontrol otomatis kipas pengering berdasarkan ambang batas suhu yang telah ditentukan.

Dengan arsitektur ini, proses pengambilan keputusan dapat dilakukan secara lokal di edge node sehingga respons lebih cepat dan sistem tetap dapat berjalan meskipun koneksi ke server pusat terputus. Dashboard berbasis web memungkinkan pemantauan kondisi pengeringan secara historis maupun real-time, serta memberikan kemudahan dalam pengelolaan data dan pengaturan sistem.

Fitur utama:
- Pengumpulan dan pemrosesan data sensor suhu & kelembapan secara lokal (Edge Computing)
- Kontrol otomatis kipas pengering berdasarkan kondisi lingkungan
- Pengiriman data ke backend untuk penyimpanan dan visualisasi
- Dashboard interaktif untuk monitoring dan analisis data pengeringan
- Dukungan firmware untuk perangkat sensor fisik (Arduino/ESP)

Proyek ini terdiri dari tiga komponen utama:
1. **CoffeeMonitor**: Backend dan dashboard berbasis Blazor (.NET) untuk visualisasi dan manajemen data.
2. **EdgeNode**: Aplikasi Python yang berjalan di perangkat edge untuk pengumpulan, pemrosesan, dan pengiriman data sensor.
3. **IoT_Sensor**: Firmware untuk perangkat sensor fisik yang membaca data lingkungan pada alat pengering.

Implementasi ini diharapkan dapat meningkatkan efisiensi dan efektivitas proses pengeringan biji kopi portable melalui pemanfaatan teknologi edge computing.

## Komponen Utama

### 1. CoffeeMonitor (Aplikasi Blazor Web)

Aplikasi `CoffeeMonitor` berfungsi sebagai backend pusat dan antarmuka pengguna (dashboard) untuk sistem.

**Fitur Utama:**
*   **Penerimaan Data via Webhook:** Menerima data sensor dari edge node melalui endpoint API webhook (`/api/iot/webhook`).
*   **Penyimpanan Data:** Menyimpan data sensor yang diterima ke dalam database SQLite menggunakan PetaPoco sebagai ORM.
*   **Dashboard Interaktif:** Menampilkan data sensor terkini dan historis (suhu, kelembapan, status kipas) menggunakan komponen MudBlazor.
    *   Menampilkan data terbaru dalam bentuk gauge.
    *   Menampilkan data historis (12 jam terakhir) dalam bentuk grafik time series.
*   **Manajemen Database:** Termasuk setup database dan skema tabel untuk `SensorDataRecord`.
*   **Konfigurasi:** Menggunakan `appsettings.json` untuk konfigurasi koneksi database dan pengaturan webhook.

**Teknologi yang Digunakan:**
*   .NET (versi target net9.0)
*   Blazor Server
*   ASP.NET Core (untuk API Webhook)
*   MudBlazor (untuk komponen UI)
*   PetaPoco (untuk akses database)
*   SQLite (sebagai database)

### 2. EdgeNode (Aplikasi Python)

Aplikasi `EdgeNode` berjalan pada perangkat edge (Raspberry Pi) untuk mengumpulkan data sensor dan mengirimkannya ke `CoffeeMonitor`.

**Fitur Utama:**
*   **Pengumpulan Data Sensor:** Membaca data suhu dan kelembapan dari sensor yang terhubung.
*   **Komunikasi MQTT:** Terhubung ke broker MQTT untuk menerima perintah atau mengirim data (berdasarkan `on_connect` dan `on_message` callbacks).
*   **Kontrol Kipas (Fan Control):** Secara otomatis mengontrol status kipas berdasarkan ambang batas suhu.
*   **Penyimpanan Data Lokal:** Menyimpan data sensor secara lokal di database SQLite sebelum mengirimkannya ke backend. Ini memastikan data tidak hilang jika koneksi ke backend terputus.
*   **Pengiriman Data ke Webhook:** Secara periodik mengirimkan batch data sensor yang terkumpul ke endpoint webhook `CoffeeMonitor`.
*   **Logging:** Menggunakan logging untuk memantau operasi dan kesalahan.

**Teknologi yang Digunakan:**
*   Python (>=3.12)
*   `paho-mqtt` (untuk komunikasi MQTT)
*   `requests` (untuk mengirim data ke webhook)
*   `sqlite3` (untuk database lokal)

### 3. IoT_Sensor (Firmware Sensor Fisik)

Komponen ini berisi kode firmware yang berjalan pada perangkat keras sensor (ESP32) yang bertugas membaca data sensor aktual dari lingkungan.

**Fitur Utama:**
*   **Pembacaan Sensor:** Membaca data dari sensor suhu dan kelembapan (DHT11).
*   **Komunikasi Data:** Mengirimkan data sensor yang telah dibaca dengan cara mempublikasikan data ke topik MQTT tertentu yang kemudian akan diterima oleh `EdgeNode`.

**Teknologi yang Digunakan (Contoh):**
*   C/C++ (untuk platform Arduino/ESP)
*   Library sensor DHT library
*   Library komunikasi PubSubClient untuk MQTT

## Struktur Proyek

Berikut adalah struktur direktori utama dari proyek ini:
```.
├── CoffeeMonitor/                  # Aplikasi Backend & Dashboard Blazor (.NET)
│   ├── Components/                 # Komponen Blazor
│   │   ├── Layout/                 # Komponen tata letak (misalnya, MainLayout.razor, NavMenu.razor)
│   │   └── Pages/                  # Halaman Blazor (misalnya, Dashboard.razor, Home.razor)
│   ├── Controllers/                # Kontroler API
│   │   └── IotWebhookController.cs # Kontroler untuk endpoint webhook IoT
│   ├── Data/                       # Direktori terkait data
│   │   ├── Migrations/             # (Jika menggunakan EF Core Migrations)
│   │   ├── Models/                 # Model entitas (misalnya, SensorDataRecord.cs, WebhookPayload.cs)
│   │   ├── Repositories/           # Repositori untuk abstraksi akses data (misalnya, SensorDataRepository.cs)
│   │   ├── CoffeeMonitor.db        # File database SQLite
│   │   └── DataContext.cs          # Konteks database (PetaPoco atau EF Core)
│   ├── Properties/                 # Pengaturan proyek
│   │   └── launchSettings.json     # Pengaturan peluncuran untuk pengembangan lokal
│   ├── wwwroot/                    # Aset statis web (CSS, JS, gambar)
│   ├── appsettings.Development.json # Pengaturan konfigurasi untuk lingkungan Development
│   ├── appsettings.json            # Pengaturan konfigurasi aplikasi utama
│   ├── CoffeeMonitor.csproj        # File proyek C#
│   ├── CoffeeMonitor.sln           # File solusi Visual Studio
│   └── Program.cs                  # Titik masuk utama aplikasi ASP.NET Core
│
├── EdgeNode/                       # Aplikasi Python untuk Edge Device
│   ├── data/                       # Direktori untuk database SQLite lokal EdgeNode
│   │   └── edge_data.db            # File database SQLite EdgeNode
│   ├── logs/                       # Direktori untuk file log EdgeNode
│   │   └── mqtt_service.log        # Contoh file log
│   ├── .python-version             # Menentukan versi Python yang digunakan
│   ├── main.py                     # Skrip utama untuk EdgeNode
│   └── pyproject.toml              # File konfigurasi proyek Python
│
├── IoT_Sensor/                     # Kode firmware untuk sensor fisik
│   └── IoT_Sensor.ino              # Sketsa Arduino/ESP untuk sensor
│
└── README.md                       # File README utama proyek
```
## Cara Menjalankan

1.  **IoT_Sensor (Perangkat IoT/ESP32):**
    *   Pastikan Anda telah menginstal Arduino IDE atau software yang sesuai untuk memprogram ESP32.
    *   Buka file `IoT_Sensor/IoT_Sensor.ino` pada Arduino IDE.
    *   Pastikan library DHT dan PubSubClient sudah terinstal di Arduino IDE.
    *   Konfigurasikan parameter WiFi, MQTT broker, dan topik MQTT pada kode sesuai jaringan dan sistem Anda.
    *   Upload firmware ke perangkat ESP32.
    *   Pastikan perangkat terhubung ke jaringan WiFi dan dapat mengirim data ke broker MQTT.

2.  **EdgeNode:**
    *   Pastikan Python dan dependensi (`paho-mqtt`, `requests`) terinstal.
    *   Konfigurasi variabel lingkungan atau konstanta dalam `main.py` (MQTT broker, URL webhook, API key).
    *   Jalankan `python main.py` pada perangkat edge.
    *   EdgeNode akan menerima data dari MQTT, mengontrol kipas, menyimpan data lokal, dan mengirim data ke backend.

3.  **CoffeeMonitor:**
    *   Pastikan .NET SDK terinstal.
    *   Konfigurasi `appsettings.json` dengan string koneksi SQLite yang benar dan API key untuk webhook.
    *   Jalankan aplikasi Blazor.
    *   Akses dashboard melalui browser untuk memantau data secara real-time dan historis.

## Pengembangan Lebih Lanjut (Potensi)

*   Implementasi autentikasi dan otorisasi yang lebih kuat.
*   Peningkatan mekanisme error handling dan retry pada `EdgeNode`.
*   Penambahan fitur notifikasi (misalnya, email atau push notification) untuk kondisi alarm.
*   Penggunaan broker MQTT yang lebih aman dan terkelola.
*   Visualisasi data yang lebih canggih di dashboard.

## Dokumentasi
[Video Proyek](https://youtu.be/ROmxKGmPCYU)

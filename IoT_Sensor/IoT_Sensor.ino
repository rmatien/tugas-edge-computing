#include <WiFi.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <PubSubClient.h> 

// ——— Wi-Fi Credentials ———————————————————————————————
const char* WIFI_SSID = "SSID_WIFI"; // Ganti dengan SSID Wifi
const char* WIFI_PASS = "PASSWORD_WIFI"; // Ganti dengan Password Wifi

// ——— Konfigurasi MQTT ————————————————————————————————
const char* MQTT_SERVER = "192.168.18.25"; // Ganti dengan IP RPi (Edge) Anda
const int MQTT_PORT = 1883;
const char* MQTT_TOPIC_PUBLISH = "sensor/data"; // Topik untuk publikasi data
const char* MQTT_TOPIC_FAN_CONTROL = "fan/control"; // Topik untuk kontrol kipas
// Jika Anda menggunakan username/password di Mosquitto (uncomment dan isi):
// const char* mqtt_username = "your_mqtt_username";
// const char* mqtt_password = "your_mqtt_password";
const char* MQTT_CLIENT_ID = "esp32-dht11-client"; // ID unik untuk klien ini
const char* FAN_CONTROLLER_ID = "esp32-dht11-client"; // ID klien yang akan mengontrol kipas

// ——— Sensor Settings ————————————————————————————————
#define DHTPIN   14        // GPIO you chose
#define DHTTYPE  DHT11

// ——— Fan Control Settings ———————————————————————————
#define FAN_RELAY_PIN 26   // GPIO pin untuk relay kipas
bool fanStatus = false;    // Status kipas (false = mati, true = hidup)

// ——— Objects ————————————————————————————————————————
WiFiClient wifiClient;
PubSubClient client(wifiClient);
DHT dht(DHTPIN, DHTTYPE);

// --- Variabel Waktu ---
unsigned long lastMsg = 0;
const long intervalPublish = 30000; // Interval publikasi data (30 detik)

// --- Fungsi Setup WiFi ---
void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Menghubungkan ke ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi terhubung");
  Serial.println("Alamat IP: ");
  Serial.println(WiFi.localIP());
}

// --- Fungsi Kontrol Kipas ---
void controlFan(bool turnOn) {
  if (turnOn) {
    // digitalWrite(FAN_RELAY_PIN, HIGH); // Nyalakan kipas
    fanStatus = true;
    Serial.println("Kipas dinyalakan");
  } else {
    // digitalWrite(FAN_RELAY_PIN, LOW); // Matikan kipas
    fanStatus = false;
    Serial.println("Kipas dimatikan");
  }
}

// --- Fungsi Callback MQTT (Untuk Menerima Pesan, jika diperlukan nanti) ---
void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Pesan diterima [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();
  
  // Buat buffer untuk menyimpan payload sebagai string
  char message[length + 1];
  for (int i = 0; i < length; i++) {
    message[i] = (char)payload[i];
    Serial.print((char)payload[i]);
  }
  message[length] = '\0'; // Null terminator
  Serial.println();
  
  // Periksa apakah pesan dari topik kontrol kipas
  if (strcmp(topic, MQTT_TOPIC_FAN_CONTROL) == 0) {
    // Cek apakah pesan mengandung target client ID
    StaticJsonDocument<256> jsonDoc;
    DeserializationError error = deserializeJson(jsonDoc, message);
    
    if (!error) {
      // Periksa apakah ada field target_client_id
      if (jsonDoc.containsKey("target_client_id")) {
        const char* targetClientId = jsonDoc["target_client_id"];
        
        // Periksa apakah pesan ditujukan untuk device ini
        if (strcmp(targetClientId, MQTT_CLIENT_ID) == 0 || strcmp(targetClientId, "all") == 0) {
          // Proses pesan kontrol kipas
          if (jsonDoc.containsKey("command")) {
            const char* command = jsonDoc["command"];
            
            if (strcmp(command, "ON") == 0 || strcmp(command, "on") == 0) {
              controlFan(true);
            } else if (strcmp(command, "OFF") == 0 || strcmp(command, "off") == 0) {
              controlFan(false);
            // } else if (strcmp(command, "AUTO") == 0 || strcmp(command, "auto") == 0) {
            //   // Mode otomatis akan diatur dalam loop utama berdasarkan suhu
            //   Serial.println("Kipas diatur ke mode otomatis");
            }
          }
        }
      }
    } else {
      Serial.println("Gagal mem-parsing JSON Payload");
    }
    Serial.println("--------------------");
  }
}

// --- Fungsi Rekoneksi MQTT ---
void reconnect() {
  // Loop sampai kita terhubung kembali
  while (!client.connected()) {
    Serial.print("Mencoba koneksi MQTT...");
    // Coba terhubung (dengan atau tanpa autentikasi)
    bool connected;
    // Uncomment blok di bawah jika menggunakan username/password
    /*
    if (client.connect(mqtt_client_id, mqtt_username, mqtt_password)) {
      connected = true;
    } else {
      connected = false;
    }
    */
    // Gunakan ini jika koneksi anonim (tanpa username/password)
    if (client.connect(MQTT_CLIENT_ID)) {
       connected = true;
    } else {
       connected = false;
    }

    if (connected) {
      Serial.println("terhubung");
      // Langganan ke topik kontrol kipas
      client.subscribe(MQTT_TOPIC_FAN_CONTROL);
      Serial.print("Berlangganan ke topik: ");
      Serial.println(MQTT_TOPIC_FAN_CONTROL);
    } else {
      Serial.print("gagal, rc=");
      Serial.print(client.state()); // Cetak kode error koneksi
      Serial.println(" coba lagi dalam 5 detik");
      // Tunggu 5 detik sebelum mencoba lagi
      delay(5000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(10);

  // Inisialisasi pin relay kipas
  // pinMode(FAN_RELAY_PIN, OUTPUT);
  // digitalWrite(FAN_RELAY_PIN, LOW); // Pastikan kipas mati saat startup

  dht.begin();
  setup_wifi();

  client.setServer(MQTT_SERVER, MQTT_PORT);
  client.setCallback(callback); // Set fungsi callback (meskipun mungkin belum digunakan)
}

void loop() {
  // Pastikan koneksi MQTT tetap terjaga
  if (!client.connected()) {
    reconnect();
  }
  client.loop(); // Proses pesan masuk/keluar MQTT

  // Kirim data secara berkala
  unsigned long now = millis();
  if (now - lastMsg > intervalPublish) {
    lastMsg = now;

    // 1. Baca data dari sensor DHT11
    float h = dht.readHumidity();
    // Baca suhu sebagai Celsius (default)
    float t = dht.readTemperature();

    // 2. Periksa apakah pembacaan berhasil (bukan NaN - Not a Number)
    if (isnan(h) || isnan(t)) {
      Serial.println("Gagal membaca dari sensor DHT!");
      return; // Lewati iterasi loop ini jika gagal baca
    }

    // 3. Buat Objek JSON menggunakan ArduinoJson
    // Tentukan ukuran buffer JSON. JSON_OBJECT_SIZE(2) cukup untuk 2 key-value pair.
    // Tambahkan sedikit buffer ekstra untuk keamanan. 128 bytes biasanya aman.
    StaticJsonDocument<256> jsonDoc;

    // Tambahkan data suhu dan kelembaban ke objek JSON
    jsonDoc["client_id"] = MQTT_CLIENT_ID;
    jsonDoc["temperature"] = t;
    jsonDoc["humidity"] = h;
    jsonDoc["fan_status"] = fanStatus ? "ON" : "OFF"; // Tambahkan status kipas ke payload

    // 4. Siapkan buffer untuk menampung string JSON
    char jsonBuffer[256];

    // 5. Serialize (ubah) objek JSON menjadi string JSON di dalam buffer
    serializeJson(jsonDoc, jsonBuffer);

    // 6. Publikasikan string JSON ke topik MQTT
    Serial.print("Mempublikasikan ke topik: ");
    Serial.println(MQTT_TOPIC_PUBLISH);
    Serial.print("Payload: ");
    Serial.println(jsonBuffer);

    bool published = client.publish(MQTT_TOPIC_PUBLISH, jsonBuffer);

    if (published) {
      Serial.println("Publikasi berhasil!");
    } else {
      Serial.println("Publikasi GAGAL!");
    }
     Serial.println("--------------------");
  }
}

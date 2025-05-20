using System.Collections.Generic;
using System.Text.Json.Serialization;


namespace CoffeeMonitor.Data.Models
{
    public class WebhookPayload
    {
        [JsonPropertyName("apiKey")]
        public string ApiKey { get; set; }

        [JsonPropertyName("deviceId")]
        public string DeviceId { get; set; }

        [JsonPropertyName("records")]
        public List<IncomingRecord> Records { get; set; }
    }

    public class IncomingRecord
    {
        // Tidak perlu Id karena Id di Python adalah primary key lokal di edge
        // Kita akan generate Id baru saat menyimpan di database pusat (Blazor)

        [JsonPropertyName("clientId")]
        public string ClientId { get; set; }

        [JsonPropertyName("temperature")]
        public double Temperature { get; set; }

        [JsonPropertyName("humidity")]
        public double Humidity { get; set; }

        [JsonPropertyName("fanStatus")]
        public string FanStatus { get; set; }

        [JsonPropertyName("timestamp")]
        public string Timestamp { get; set; }
    }
}
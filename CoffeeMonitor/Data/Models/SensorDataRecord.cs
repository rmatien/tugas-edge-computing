using PetaPoco;
using System;

namespace CoffeeMonitor.Data.Models
{
    [TableName("SensorData")]
    [PrimaryKey("Id", AutoIncrement = true)]
    public class SensorDataRecord
    {
        public long Id { get; set; } // Primary key di database Blazor
        public string ClientId { get; set; }
        public double Temperature { get; set; }
        public double Humidity { get; set; }
        public string FanStatus { get; set; }
        public string Timestamp { get; set; } // Simpan sebagai string ISO format
        public DateTime ReceivedAt { get; set; } = DateTime.UtcNow; // Waktu data diterima oleh webhook
    }
}
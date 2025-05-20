using CoffeeMonitor.Data.Models;
using CoffeeMonitor.Data.Repositories;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using System;
using System.Linq;
using System.Threading.Tasks;

namespace CoffeeMonitor.Controllers
{
    [Route("api/iot")] // Base route untuk API IoT
    [ApiController]
    public class IotWebhookController : ControllerBase
    {
        private readonly ISensorDataRepository _repository;
        private readonly ILogger<IotWebhookController> _logger;
        private readonly string _expectedApiKey;

        public IotWebhookController(ISensorDataRepository repository, IConfiguration configuration, ILogger<IotWebhookController> logger)
        {
            _repository = repository;
            _logger = logger;
            _expectedApiKey = configuration["WebhookSettings:ApiKey"]; // Ambil API Key dari config
        }

        [HttpPost("webhook")] // Endpoint: /api/iot/webhook
        public async Task<IActionResult> PostSensorData([FromBody] WebhookPayload payload)
        {
            // 1. Validasi API Key (Optional tapi direkomendasikan)
            if (string.IsNullOrEmpty(_expectedApiKey) || payload.ApiKey != _expectedApiKey)
            {
                _logger.LogWarning("Unauthorized webhook attempt. Invalid or missing API Key.");
                return Unauthorized("Invalid API Key");
            }

            // 2. Validasi Payload
            if (payload == null || payload.Records == null || !payload.Records.Any())
            {
                _logger.LogWarning("Received empty or invalid payload.");
                return BadRequest("Payload cannot be empty.");
            }

            _logger.LogInformation($"Received {payload.Records.Count} records from device {payload.DeviceId ?? "Unknown"}.");

            try
            {
                // 3. Transformasi data dari IncomingRecord ke SensorDataRecord
                var dataToSave = payload.Records.Select(r => new SensorDataRecord
                {
                    ClientId = r.ClientId,
                    Temperature = r.Temperature,
                    Humidity = r.Humidity,
                    FanStatus = r.FanStatus,
                    Timestamp = r.Timestamp, // Simpan timestamp asli dari edge
                    ReceivedAt = DateTime.UtcNow // Tambahkan timestamp saat diterima server
                });

                // 4. Simpan data menggunakan repository
                await _repository.AddSensorDataBatchAsync(dataToSave);

                _logger.LogInformation($"Successfully saved {dataToSave.Count()} records to the database.");
                return Ok($"Received {dataToSave.Count()} records successfully."); // Respon sukses
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error processing webhook data.");
                return StatusCode(500, "Internal server error while processing data."); // Respon error server
            }
        }
    }
}
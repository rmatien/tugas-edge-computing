using CoffeeMonitor.Data.Models;
using System; // Tambahkan using System
using System.Collections.Generic;
using System.Threading.Tasks;

namespace CoffeeMonitor.Data.Repositories
{
    public interface ISensorDataRepository
    {
        Task AddSensorDataBatchAsync(IEnumerable<SensorDataRecord> records);
        Task<IEnumerable<SensorDataRecord>> GetRecentSensorDataAsync(int count);
        // Method baru untuk mengambil data berdasarkan rentang waktu
        Task<IEnumerable<SensorDataRecord>> GetSensorDataByDateRangeAsync(DateTime startTime, DateTime endTime);
    }
}
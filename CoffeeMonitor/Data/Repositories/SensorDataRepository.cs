using CoffeeMonitor.Data.Models;

namespace CoffeeMonitor.Data.Repositories
{
    public class SensorDataRepository : ISensorDataRepository
    {
        private readonly DBContext _context;
        // private readonly ILogger<SensorDataRepository> _logger; // Opsional: Tambahkan logger

        public SensorDataRepository(DBContext context)
        {
            _context = context;            
            // _logger = logger; // Jika pakai logger
        }

        public async Task AddSensorDataBatchAsync(IEnumerable<SensorDataRecord> records)
        {
             if (records == null || !records.Any())
                return;

            try
            {
                var db = _context.GetDatabase();

                // PetaPoco mendukung transaksi untuk operasi batch
                using (var scope = db.GetTransaction())
                {
                    foreach (var record in records)
                    {
                        // Set ReceivedAt jika belum di-set
                        if (record.ReceivedAt == default)
                        {
                            record.ReceivedAt = DateTime.UtcNow;
                        }
                        await db.InsertAsync(record);
                    }
                    scope.Complete(); // Commit transaksi
                }
            }
            catch (Exception ex)
            {
                // Log error
                Console.WriteLine($"Error saving batch data: {ex.Message}");
                // Handle atau throw ulang sesuai kebutuhan
                throw;
            }
        }

         public async Task<IEnumerable<SensorDataRecord>> GetRecentSensorDataAsync(int count)
        {
            try
            {
                var db = _context.GetDatabase();

                // Ambil 'count' data terbaru berdasarkan ReceivedAt
                var sql = "select * from SensorData order by ReceivedAt desc limit @0;";
                return await db.FetchAsync<SensorDataRecord>(sql, count);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error fetching recent data: {ex.Message}");
                return Enumerable.Empty<SensorDataRecord>(); // Kembalikan list kosong jika error
            }
        }

        // Implementasi method baru
        public async Task<IEnumerable<SensorDataRecord>> GetSensorDataByDateRangeAsync(DateTime startTime, DateTime endTime)
        {
            try
            {
                var db = _context.GetDatabase();

                // Pastikan format DateTime sesuai dengan penyimpanan di SQLite (biasanya ISO 8601: "yyyy-MM-dd HH:mm:ss.fff")
                // PetaPoco biasanya menangani konversi DateTime ke format string yang benar untuk query
                var sql = "select * from SensorData where ReceivedAt >= @0 AND ReceivedAt <= @1 order by ReceivedAt;";
                return await db.FetchAsync<SensorDataRecord>(sql, startTime, endTime);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error fetching data by date range: {ex.Message}");
                // _logger?.LogError(ex, "Error fetching data by date range from {StartTime} to {EndTime}", startTime, endTime); // Jika pakai logger
                return Enumerable.Empty<SensorDataRecord>();
            }
        }
    }
}
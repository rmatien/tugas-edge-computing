namespace CoffeeMonitor.Data
{
    public static class DatabaseSetup
    {
        public static void InitializeDatabase(DBContext dbContext) // Modified parameter
        {
            var connectionString = dbContext.GetConnectionString();

            if (string.IsNullOrEmpty(connectionString))
            {
                Console.WriteLine("Error: Database connection string not available from DBContext.");
                throw new InvalidOperationException("Database connection string not available from DBContext.");
            }

            string actualDbFilePath;
            if (connectionString.StartsWith("Data Source=", StringComparison.OrdinalIgnoreCase))
            {
                actualDbFilePath = connectionString.Substring("Data Source=".Length);
            }
            else
            {
                // This case might need adjustment if your connection string format changes
                actualDbFilePath = connectionString; 
            }

            var dbDirectory = Path.GetDirectoryName(actualDbFilePath);

            if (!string.IsNullOrEmpty(dbDirectory) && !Directory.Exists(dbDirectory))
            {
                Directory.CreateDirectory(dbDirectory);
                Console.WriteLine($"Created database directory: {dbDirectory}");
            }

            // Get IDatabase instance from DBContext
            using (var db = dbContext.GetDatabase()) 
            {
                try
                {
                    var tableExists = db.ExecuteScalar<int>("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='SensorData';") > 0;

                    if (!tableExists)
                    {
                        Console.WriteLine("SensorData table not found. Creating table...");
                        db.Execute(@"
                        CREATE TABLE SensorData (
                            Id INTEGER PRIMARY KEY AUTOINCREMENT,
                            ClientId TEXT NULL,
                            Temperature REAL NOT NULL,
                            Humidity REAL NOT NULL,
                            FanStatus TEXT NULL,
                            Timestamp TEXT NULL,
                            ReceivedAt TEXT NOT NULL
                        );");
                        Console.WriteLine("SensorData table created successfully.");
                    }
                    else
                    {
                         Console.WriteLine("SensorData table already exists.");
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error initializing database: {ex.Message}");
                    throw;
                }
            }
        }
    }
}
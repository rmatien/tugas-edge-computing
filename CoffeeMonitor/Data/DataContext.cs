using Microsoft.Extensions.Options;
using System.Globalization;
using PetaPoco;
using PetaPoco.Providers;

namespace CoffeeMonitor.Data
{
    public class DBContext
    {
        private readonly string? _connectionString;

        public DBContext(IOptions<DatabaseOptions> databaseOptions)
        {
            _connectionString = databaseOptions.Value.DefaultConnection;
        }

        public IDatabase GetDatabase()
        {
            var builder = DatabaseConfiguration.Build()
                .UsingConnectionString(_connectionString)
                .UsingProvider<SQLiteDatabaseProvider>()
                .UsingDefaultMapper<ConventionMapper>(m =>
                {
                    m.FromDbConverter = (targetProperty, sourceType) =>
                    {
                        if (targetProperty != null && sourceType == typeof(long))
                        {
                            var type = Nullable.GetUnderlyingType(targetProperty.PropertyType) ?? targetProperty.PropertyType;

                            switch (Type.GetTypeCode(type))
                            {
                                case TypeCode.DateTime:
                                    return o => DateTime.ParseExact(o.ToString(), "yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal);
                                case TypeCode.Boolean:
                                    return o => Convert.ToInt64(o) == 1;
                                default:
                                    return o => Convert.ChangeType(o, Type.GetTypeCode(type));
                            }
                        }

                        return null;
                    };
                    m.ToDbConverter = sourceProperty =>
                    {
                        var type = Nullable.GetUnderlyingType(sourceProperty.PropertyType) ?? sourceProperty.PropertyType;

                        switch (Type.GetTypeCode(type))
                        {
                            case TypeCode.DateTime:
                                return o => ((DateTime)o).ToString("yyyy-MM-dd HH:mm:ss");
                            case TypeCode.Boolean:
                                return o => ((bool)o) ? 1 : 0;
                        }

                        return null;
                    };
                });

            var db = builder.Create();
            return db;
        }

        public string? GetConnectionString() {
            return _connectionString;
        }
    }

    public class DatabaseOptions
    {
        public string? DefaultConnection { get; set; }
    }
}
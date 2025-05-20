using MudBlazor.Services;
using CoffeeMonitor.Components;
using CoffeeMonitor.Data;
using CoffeeMonitor.Data.Repositories;

var builder = WebApplication.CreateBuilder(args);

// Configure SQLite database
builder.Services.Configure<DatabaseOptions>(builder.Configuration.GetSection("ConnectionStrings"));
builder.Services.AddSingleton<DBContext>();

// Daftarkan Repository
builder.Services.AddScoped<ISensorDataRepository, SensorDataRepository>();

// Add MudBlazor services
builder.Services.AddMudServices();

// Add services to the container.
builder.Services.AddRazorComponents()
    .AddInteractiveServerComponents();

// Tambahkan Controller untuk API
builder.Services.AddControllers();

// Daftarkan Logging
builder.Services.AddLogging();

var app = builder.Build();

// Panggil Database Setup setelah app di-build tapi sebelum Run
try
{
    // Resolve DBContext from services
    using (var scope = app.Services.CreateScope())
    {
        var dbContext = scope.ServiceProvider.GetRequiredService<DBContext>();
        DatabaseSetup.InitializeDatabase(dbContext); // Pass DBContext instance
    }
}
catch (Exception ex)
{
    var logger = app.Services.GetRequiredService<ILogger<Program>>();
    logger.LogCritical(ex, "Failed to initialize the database.");
    Environment.Exit(1); 
}

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error", createScopeForErrors: true);
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

app.UseHttpsRedirection();

app.UseStaticFiles(); // Pastikan ini ada sebelum MapRazorComponents

app.UseAntiforgery(); // Komentari atau hapus jika menyebabkan masalah pada API POST

// Tambahkan routing untuk API Controller
app.MapControllers(); // Ini akan memetakan route di controller Anda

app.MapStaticAssets();
app.MapRazorComponents<App>()
    .AddInteractiveServerRenderMode();

app.Run();

using System.Text;
using FluentValidation;
using MediatR;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Microsoft.OpenApi.Models;
using MedAgent.Api.Middleware;
using MedAgent.Api.Swagger;
using MedAgent.Application.Interfaces;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Domain.Interfaces;
using MedAgent.Infrastructure.Data;
using MedAgent.Infrastructure.Repositories;
using MedAgent.Infrastructure.Services;

var builder = WebApplication.CreateBuilder(args);

// ──────────────────────────────── Database ────────────────────────────────
var configuredConnString = builder.Configuration.GetConnectionString("Default");
if (string.IsNullOrWhiteSpace(configuredConnString))
{
    configuredConnString = null;
}

// Docker compose mounts a persistent volume at /app/data in the runtime container.
// In local dev, we keep the DB next to the API by default.
var dbPath = builder.Environment.IsProduction()
    ? Path.Combine(builder.Environment.ContentRootPath, "data", "medagent.db")
    : Path.Combine(builder.Environment.ContentRootPath, "medagent.db");

Directory.CreateDirectory(Path.GetDirectoryName(dbPath)!);
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseSqlite(configuredConnString ?? $"Data Source={dbPath}"));

// ──────────────────────────────── Dependency Injection ────────────────────
// Domain
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IPhotoRepository, PhotoRepository>();
builder.Services.AddScoped<IMedicineRepository, MedicineRepository>();

// Application
builder.Services.AddScoped<IAuthService, AuthService>();
builder.Services.AddMediatR(cfg => cfg.RegisterServicesFromAssembly(typeof(RegisterUserCommand).Assembly));
builder.Services.AddValidatorsFromAssembly(typeof(RegisterUserCommand).Assembly);
builder.Services.AddTransient(typeof(IPipelineBehavior<,>), typeof(ValidationBehavior<,>));

// ──────────────────────────────── Authentication ──────────────────────────
var jwtSecret = builder.Configuration["Jwt:Secret"] ?? "MedAgent-Dev-Secret-Key-Change-In-Production-2024!@#$";
var jwtIssuer = builder.Configuration["Jwt:Issuer"] ?? "MedAgent";
var jwtAudience = builder.Configuration["Jwt:Audience"] ?? "MedAgentApp";

builder.Services.AddAuthentication(options =>
{
    options.DefaultAuthenticateScheme = JwtBearerDefaults.AuthenticationScheme;
    options.DefaultChallengeScheme = JwtBearerDefaults.AuthenticationScheme;
})
.AddJwtBearer(options =>
{
    options.TokenValidationParameters = new TokenValidationParameters
    {
        ValidateIssuer = true,
        ValidateAudience = true,
        ValidateLifetime = true,
        ValidateIssuerSigningKey = true,
        ValidIssuer = jwtIssuer,
        ValidAudience = jwtAudience,
        IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtSecret)),
        ClockSkew = TimeSpan.Zero
    };
});
builder.Services.AddAuthorization();

// ──────────────────────────────── CORS ────────────────────────────────────
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowFrontend", policy =>
    {
        policy.WithOrigins(
                "http://localhost:5173",  // Vite dev server
                "http://localhost:4173",  // Vite preview
                "http://localhost:8080"   // Docker
            )
            .AllowAnyHeader()
            .AllowAnyMethod()
            .AllowCredentials();
    });
});

// ──────────────────────────────── Controllers & Swagger ───────────────────
builder.Services.AddControllers();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen(c =>
{
    c.SwaggerDoc("v1", new OpenApiInfo
    {
        Title = "MedAgent API",
        Version = "v1",
        Description = "Backend API for MedAgent — your AI medical assistant."
    });

    c.AddSecurityDefinition("Bearer", new OpenApiSecurityScheme
    {
        Description = "JWT Authorization header using the Bearer scheme. Enter 'Bearer' [space] and then your token.",
        Name = "Authorization",
        In = ParameterLocation.Header,
        Type = SecuritySchemeType.ApiKey,
        Scheme = "Bearer"
    });

    c.AddSecurityRequirement(new OpenApiSecurityRequirement
    {
        {
            new OpenApiSecurityScheme
            {
                Reference = new OpenApiReference
                {
                    Type = ReferenceType.SecurityScheme,
                    Id = "Bearer"
                }
            },
            Array.Empty<string>()
        }
    });

    // Fix Swagger generation for endpoints that use [FromForm] IFormFile (multipart/form-data uploads)
    c.OperationFilter<FormFileOperationFilter>();
});

var app = builder.Build();

// ──────────────────────────────── Middleware Pipeline ─────────────────────
app.UseMiddleware<ExceptionMiddleware>();

var swaggerEnabled = app.Environment.IsDevelopment() || builder.Configuration.GetValue<bool>("Swagger:Enabled");
if (swaggerEnabled)
{
    app.UseSwagger();
    app.UseSwaggerUI(c => c.SwaggerEndpoint("/swagger/v1/swagger.json", "MedAgent API v1"));
}

// Serve the Vite SPA static files (for Docker deployment)
app.UseDefaultFiles();
app.UseStaticFiles();

app.UseCors("AllowFrontend");

app.UseAuthentication();
app.UseAuthorization();

app.MapControllers();

// SPA fallback — serve index.html for non-API routes (for Docker deployment)
app.MapFallbackToFile("index.html");

// ──────────────────────────────── Auto-Migrate ───────────────────────────
using (var scope = app.Services.CreateScope())
{
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    db.Database.EnsureCreated();
    db.Database.ExecuteSqlRaw(@"CREATE TABLE IF NOT EXISTS ""Medicines"" (
    ""Id"" TEXT NOT NULL CONSTRAINT ""PK_Medicines"" PRIMARY KEY,
    ""UserId"" TEXT NOT NULL,
    ""Name"" TEXT NOT NULL DEFAULT '',
    ""Dosage"" TEXT NOT NULL DEFAULT '',
    ""Desc"" TEXT NOT NULL DEFAULT '',
    ""Type"" TEXT NOT NULL DEFAULT 'Chronic Care',
    ""Freq"" TEXT NOT NULL DEFAULT '',
    ""Time"" TEXT NOT NULL DEFAULT '',
    ""Supply"" TEXT NOT NULL DEFAULT '30',
    ""Status"" TEXT NOT NULL DEFAULT 'scheduled',
    ""Archived"" INTEGER NOT NULL DEFAULT 0,
    ""Category"" TEXT NOT NULL DEFAULT 'primary',
    ""CreatedAt"" TEXT NOT NULL DEFAULT (datetime('now')),
    CONSTRAINT ""FK_Medicines_Users_UserId"" FOREIGN KEY (""UserId"") REFERENCES ""Users"" (""Id"") ON DELETE CASCADE
)");
    db.Database.ExecuteSqlRaw(@"CREATE INDEX IF NOT EXISTS ""IX_Medicines_UserId"" ON ""Medicines"" (""UserId"")");
}

app.Run();
// var port = Environment.GetEnvironmentVariable("PORT") ?? "10000";
// app.Run($"http://0.0.0.0:{port}");

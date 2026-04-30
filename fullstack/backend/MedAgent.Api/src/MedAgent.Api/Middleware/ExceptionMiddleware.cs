using System.Net;
using System.Text.Json;
using FluentValidation;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Hosting;

namespace MedAgent.Api.Middleware;

/// <summary>
/// Global exception handling middleware that catches exceptions thrown
/// throughout the pipeline and returns standardized JSON error responses.
/// </summary>
public class ExceptionMiddleware
{
    private readonly RequestDelegate _next;
    private readonly ILogger<ExceptionMiddleware> _logger;
    private readonly IHostEnvironment _environment;

    public ExceptionMiddleware(RequestDelegate next, ILogger<ExceptionMiddleware> logger, IHostEnvironment environment)
    {
        _next = next;
        _logger = logger;
        _environment = environment;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        try
        {
            await _next(context);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "An unhandled exception occurred: {Message}", ex.Message);
            await HandleExceptionAsync(context, ex, _environment);
        }
    }

    private static async Task HandleExceptionAsync(HttpContext context, Exception exception, IHostEnvironment environment)
    {
        context.Response.ContentType = "application/json";

        var (statusCode, response) = exception switch
        {
            ValidationException validationEx => (
                (int)HttpStatusCode.BadRequest,
                new ErrorResponse
                {
                    Status = (int)HttpStatusCode.BadRequest,
                    Title = "Validation Failed",
                    Errors = validationEx.Errors
                        .GroupBy(e => e.PropertyName)
                        .ToDictionary(
                            g => g.Key,
                            g => g.Select(e => e.ErrorMessage).ToArray())
                }
            ),

            UnauthorizedAccessException => (
                (int)HttpStatusCode.Unauthorized,
                new ErrorResponse
                {
                    Status = (int)HttpStatusCode.Unauthorized,
                    Title = exception.Message
                }
            ),

            ApplicationException => (
                (int)HttpStatusCode.Conflict,
                new ErrorResponse
                {
                    Status = (int)HttpStatusCode.Conflict,
                    Title = exception.Message
                }
            ),

            KeyNotFoundException => (
                (int)HttpStatusCode.NotFound,
                new ErrorResponse
                {
                    Status = (int)HttpStatusCode.NotFound,
                    Title = exception.Message
                }
            ),

            DbUpdateConcurrencyException => (
                (int)HttpStatusCode.Conflict,
                new ErrorResponse
                {
                    Status = (int)HttpStatusCode.Conflict,
                    Title = exception.Message
                }
            ),

            _ => (
                (int)HttpStatusCode.InternalServerError,
                new ErrorResponse
                {
                    Status = (int)HttpStatusCode.InternalServerError,
                    Title = environment.IsDevelopment()
                        ? exception.GetType().Name + ": " + exception.Message
                        : "An unexpected error occurred.",
                    Detail = environment.IsDevelopment() ? exception.ToString() : null
                }
            )
        };

        context.Response.StatusCode = statusCode;

        var jsonOptions = new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase };
        await context.Response.WriteAsync(JsonSerializer.Serialize(response, jsonOptions));
    }
}

public class ErrorResponse
{
    public int Status { get; set; }
    public string Title { get; set; } = string.Empty;
    public Dictionary<string, string[]>? Errors { get; set; }
    public string? Detail { get; set; }
}

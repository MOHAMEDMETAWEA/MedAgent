using System.Reflection;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.OpenApi.Models;
using Swashbuckle.AspNetCore.SwaggerGen;

namespace MedAgent.Api.Swagger;

/// <summary>
/// Swashbuckle doesn't auto-handle [FromForm] IFormFile parameters.
/// This operation filter converts such actions into a multipart/form-data request body schema,
/// so Swagger UI can render a file picker and generate correct requests.
/// </summary>
public sealed class FormFileOperationFilter : IOperationFilter
{
    public void Apply(OpenApiOperation operation, OperationFilterContext context)
    {
        var parameters = context.ApiDescription.ParameterDescriptions;

        var fromFormParams = parameters
            .Where(p => p.Source?.Id == "Form" || p.CustomAttributes().OfType<FromFormAttribute>().Any())
            .ToList();

        if (fromFormParams.Count == 0)
        {
            return;
        }

        var hasFile = fromFormParams.Any(p =>
            typeof(IFormFile).IsAssignableFrom(p.Type) ||
            (p.Type.IsGenericType && p.Type.GetGenericTypeDefinition() == typeof(IEnumerable<>) &&
             typeof(IFormFile).IsAssignableFrom(p.Type.GetGenericArguments()[0])));

        if (!hasFile)
        {
            return;
        }

        operation.Parameters.Clear();

        var schema = new OpenApiSchema
        {
            Type = "object",
            Properties = new Dictionary<string, OpenApiSchema>(),
            Required = new HashSet<string>()
        };

        foreach (var p in fromFormParams)
        {
            var name = p.Name ?? "file";
            var isRequired = p.IsRequired;

            OpenApiSchema propSchema;

            if (typeof(IFormFile).IsAssignableFrom(p.Type))
            {
                propSchema = new OpenApiSchema { Type = "string", Format = "binary" };
            }
            else
            {
                // Basic fallback for common scalar form fields
                propSchema = p.Type == typeof(int) || p.Type == typeof(int?)
                    ? new OpenApiSchema { Type = "integer", Format = "int32" }
                    : p.Type == typeof(long) || p.Type == typeof(long?)
                        ? new OpenApiSchema { Type = "integer", Format = "int64" }
                        : p.Type == typeof(bool) || p.Type == typeof(bool?)
                            ? new OpenApiSchema { Type = "boolean" }
                            : new OpenApiSchema { Type = "string" };
            }

            schema.Properties[name] = propSchema;
            if (isRequired) schema.Required.Add(name);
        }

        operation.RequestBody = new OpenApiRequestBody
        {
            Required = true,
            Content =
            {
                ["multipart/form-data"] = new OpenApiMediaType
                {
                    Schema = schema
                }
            }
        };
    }
}


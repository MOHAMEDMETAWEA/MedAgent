namespace MedAgent.Application.DTOs;

public class PhotoDto
{
    public Guid Id { get; set; }
    public string Category { get; set; } = "General";
    public string FileName { get; set; } = string.Empty;
    public string ContentType { get; set; } = "image/jpeg";
    public DateTime CreatedAt { get; set; }
    public string? Url { get; set; } // Will be populated by the controller/service
}

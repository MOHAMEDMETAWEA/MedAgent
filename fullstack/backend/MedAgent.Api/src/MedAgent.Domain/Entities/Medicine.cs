using System.Text.Json.Serialization;
namespace MedAgent.Domain.Entities;

public class Medicine
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid UserId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Dosage { get; set; } = string.Empty;
    public string Desc { get; set; } = string.Empty;
    public string Type { get; set; } = "Chronic Care";
    public string Freq { get; set; } = string.Empty;
    public string Time { get; set; } = string.Empty;
    public string Supply { get; set; } = "30";
    public string Status { get; set; } = "scheduled";
    public bool Archived { get; set; } = false;
    public string Category { get; set; } = "primary";
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [JsonIgnore]
    public virtual User? User { get; set; }
}

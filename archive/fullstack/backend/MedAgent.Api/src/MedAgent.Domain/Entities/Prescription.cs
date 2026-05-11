using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace MedAgent.Domain.Entities;

public class Prescription
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid UserId { get; set; }
    
    [Required]
    public string Name { get; set; } = string.Empty;
    public string Freq { get; set; } = string.Empty; // e.g. "Once daily"
    public string Time { get; set; } = string.Empty; // e.g. "Morning • 8:00 AM"

    [JsonIgnore]
    public virtual User User { get; set; } = null!;
}

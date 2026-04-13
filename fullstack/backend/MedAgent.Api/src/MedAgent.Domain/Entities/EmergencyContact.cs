using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace MedAgent.Domain.Entities;

public class EmergencyContact
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid UserId { get; set; }
    
    [Required]
    public string Name { get; set; } = string.Empty;
    
    [Required]
    public string Phone { get; set; } = string.Empty;
    
    public string Relation { get; set; } = string.Empty;
    
    public string AvatarUrl { get; set; } = string.Empty;
    
    public string Type { get; set; } = "family"; // family or medical

    [JsonIgnore]
    public virtual User User { get; set; } = null!;
}

using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace MedAgent.Domain.Entities;

public class ChronicCondition
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid UserId { get; set; }
    
    [Required]
    public string Name { get; set; } = string.Empty;
    public string Description { get; set; } = string.Empty;

    [JsonIgnore]
    public virtual User User { get; set; } = null!;
}

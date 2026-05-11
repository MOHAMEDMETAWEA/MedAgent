using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;

namespace MedAgent.Domain.Entities;

public class InsuranceData
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public Guid UserId { get; set; }
    
    public string ProviderName { get; set; } = string.Empty;
    public string MemberId { get; set; } = string.Empty;
    public string GroupNumber { get; set; } = string.Empty;
    public string PlanType { get; set; } = string.Empty;
    public string CardImageUrl { get; set; } = string.Empty;

    [JsonIgnore]
    public virtual User User { get; set; } = null!;
}

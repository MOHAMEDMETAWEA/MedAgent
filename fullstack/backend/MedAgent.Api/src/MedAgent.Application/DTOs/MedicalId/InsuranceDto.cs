namespace MedAgent.Application.DTOs.MedicalId;

public class InsuranceDto
{
    public string ProviderName { get; set; } = string.Empty;
    public string MemberId { get; set; } = string.Empty;
    public string GroupNumber { get; set; } = string.Empty;
    public string PlanType { get; set; } = string.Empty;
    public string CardImage { get; set; } = string.Empty; // Maps to CardImageUrl
}

namespace MedAgent.Application.DTOs.MedicalId;

public class EmergencyContactDto
{
    public Guid? Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Phone { get; set; } = string.Empty;
    public string Relation { get; set; } = string.Empty;
    public string Avatar { get; set; } = string.Empty; // Maps to AvatarUrl
    public string Type { get; set; } = "family";
}

namespace MedAgent.Application.DTOs;

public class UpdateUserProfileDto
{
    public string? FirstName { get; set; }
    public string? LastName { get; set; }
    public string? ProfileImage { get; set; }
    public string? BloodType { get; set; }
    public string? Gender { get; set; }
    public DateTime? DateOfBirth { get; set; }
}

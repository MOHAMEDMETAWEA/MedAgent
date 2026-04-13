namespace MedAgent.Application.DTOs;

public class RegisterUserDto
{
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string Password { get; set; } = string.Empty;
    public string? ProfileImage { get; set; } // Still received as Base64 for ease of use in 1-step registration
    public string BloodType { get; set; } = "Unknown";
    public string Gender { get; set; } = "M";
    public DateTime? DateOfBirth { get; set; }
}

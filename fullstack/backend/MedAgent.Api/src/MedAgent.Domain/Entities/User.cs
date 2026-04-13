namespace MedAgent.Domain.Entities;

public class User
{
    public Guid Id { get; set; } = Guid.NewGuid();
    public string PatientId { get; set; } = GeneratePatientId();
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string PasswordHash { get; set; } = string.Empty;
    
    // Auth & Identity
    public Guid? ProfileImageId { get; set; }
    public virtual ICollection<UserPhoto> Photos { get; set; } = new List<UserPhoto>();
    
    // Medical Profile
    public string BloodType { get; set; } = "Unknown";
    public string Gender { get; set; } = "M";
    public string Weight { get; set; } = string.Empty;
    public string Height { get; set; } = string.Empty;
    public string NationalId { get; set; } = string.Empty;
    public string OrganDonor { get; set; } = string.Empty;
    public string AdvanceDirectives { get; set; } = string.Empty;
    
    public DateTime? DateOfBirth { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation Properties
    public virtual InsuranceData? Insurance { get; set; }
    public virtual ICollection<EmergencyContact> EmergencyContacts { get; set; } = new List<EmergencyContact>();
    public virtual ICollection<Allergy> Allergies { get; set; } = new List<Allergy>();
    public virtual ICollection<ChronicCondition> ChronicConditions { get; set; } = new List<ChronicCondition>();
    public virtual ICollection<Prescription> Prescriptions { get; set; } = new List<Prescription>();

    private static string GeneratePatientId()
    {
        var random = new Random();
        return $"#MED-{random.Next(100, 999)}-{random.Next(100, 999)}";
    }
}

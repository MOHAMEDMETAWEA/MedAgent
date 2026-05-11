using System;
using System.Collections.Generic;

namespace MedAgent.Application.DTOs.MedicalId;

public class MedicalIdDto
{
    public string FirstName { get; set; } = string.Empty;
    public string LastName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
    public string PatientId { get; set; } = string.Empty;
    public string BloodType { get; set; } = "Unknown";
    public string Gender { get; set; } = "M";
    public Guid? ProfileImageId { get; set; }
    public string Weight { get; set; } = string.Empty;
    public string Height { get; set; } = string.Empty;
    public string NationalId { get; set; } = string.Empty;
    public string OrganDonor { get; set; } = string.Empty;
    public string AdvanceDirectives { get; set; } = string.Empty;
    
    public List<AllergyDto> Allergies { get; set; } = new();
    public List<ChronicConditionDto> ChronicConditions { get; set; } = new();
    public List<PrescriptionDto> Prescriptions { get; set; } = new();

    public InsuranceDto Insurance { get; set; } = new();
    public List<EmergencyContactDto> EmergencyContacts { get; set; } = new();
}

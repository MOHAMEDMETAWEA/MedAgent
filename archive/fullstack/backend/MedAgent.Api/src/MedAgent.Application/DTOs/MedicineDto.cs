namespace MedAgent.Application.DTOs;

public class MedicineDto
{
    public Guid? Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string Dosage { get; set; } = string.Empty;
    public string Desc { get; set; } = string.Empty;
    public string Type { get; set; } = "Chronic Care";
    public string Freq { get; set; } = string.Empty;
    public string Time { get; set; } = string.Empty;
    public string Supply { get; set; } = "30";
    public string Status { get; set; } = "scheduled";
    public bool Archived { get; set; } = false;
    public string Category { get; set; } = "primary";
}

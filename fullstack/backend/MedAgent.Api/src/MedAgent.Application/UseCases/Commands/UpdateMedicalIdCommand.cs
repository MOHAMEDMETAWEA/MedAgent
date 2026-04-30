using MediatR;
using MedAgent.Application.DTOs.MedicalId;
using MedAgent.Domain.Interfaces;
using MedAgent.Domain.Entities;
using System.Linq;

namespace MedAgent.Application.UseCases.Commands;

public record UpdateMedicalIdCommand(Guid UserId, MedicalIdDto Dto) : IRequest<bool>;

public class UpdateMedicalIdCommandHandler : IRequestHandler<UpdateMedicalIdCommand, bool>
{
    private readonly IUserRepository _userRepository;

    public UpdateMedicalIdCommandHandler(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    public async Task<bool> Handle(UpdateMedicalIdCommand request, CancellationToken cancellationToken)
    {
        var dto = request.Dto;
        // Normalize null collections from JSON (explicit null overrides property initializers).
        dto.Allergies ??= new List<AllergyDto>();
        dto.ChronicConditions ??= new List<ChronicConditionDto>();
        dto.Prescriptions ??= new List<PrescriptionDto>();
        dto.EmergencyContacts ??= new List<EmergencyContactDto>();
        dto.Insurance ??= new InsuranceDto();

        var user = await _userRepository.GetByIdForMedicalUpdateAsync(request.UserId);
        if (user == null) throw new KeyNotFoundException("User not found.");

        // Update User Metadata
        user.FirstName = dto.FirstName;
        user.LastName = dto.LastName;
        user.BloodType = dto.BloodType;
        user.Gender = dto.Gender;
        
        if (dto.ProfileImageId.HasValue) 
        {
            user.ProfileImageId = dto.ProfileImageId;
        }
        
        user.Weight = dto.Weight;
        user.Height = dto.Height;
        user.NationalId = dto.NationalId;
        user.OrganDonor = dto.OrganDonor;
        user.AdvanceDirectives = dto.AdvanceDirectives;
        
        // Update Collections (Allergies, Conditions, Prescriptions) - Only if provided to prevent accidental wipes during partial updates
        if (dto.Allergies.Any())
        {
            user.Allergies.Clear();
            foreach (var a in dto.Allergies)
            {
                user.Allergies.Add(new Allergy { UserId = user.Id, Name = a.Name, Severity = a.Severity });
            }
        }

        if (dto.ChronicConditions.Any())
        {
            user.ChronicConditions.Clear();
            foreach (var c in dto.ChronicConditions)
            {
                user.ChronicConditions.Add(new ChronicCondition { UserId = user.Id, Name = c.Name, Description = c.Description });
            }
        }

        if (dto.Prescriptions.Any())
        {
            user.Prescriptions.Clear();
            foreach (var p in dto.Prescriptions)
            {
                user.Prescriptions.Add(new Prescription { UserId = user.Id, Name = p.Name, Freq = p.Freq, Time = p.Time });
            }
        }

        // Update Insurance
        if (user.Insurance == null)
        {
            user.Insurance = new InsuranceData { UserId = user.Id };
        }
        user.Insurance.ProviderName = dto.Insurance.ProviderName;
        user.Insurance.MemberId = dto.Insurance.MemberId;
        user.Insurance.GroupNumber = dto.Insurance.GroupNumber;
        user.Insurance.PlanType = dto.Insurance.PlanType;
        user.Insurance.CardImageUrl = dto.Insurance.CardImage;

        // Update Emergency Contacts (Replacement approach for simplicity/safety in batch)
        user.EmergencyContacts.Clear();
        foreach (var contactDto in dto.EmergencyContacts)
        {
            user.EmergencyContacts.Add(new EmergencyContact
            {
                UserId = user.Id,
                Name = contactDto.Name,
                Phone = contactDto.Phone,
                Relation = contactDto.Relation,
                AvatarUrl = contactDto.Avatar,
                Type = contactDto.Type
            });
        }

        user.UpdatedAt = DateTime.UtcNow;
        await _userRepository.UpdateAsync(user);

        return true;
    }
}

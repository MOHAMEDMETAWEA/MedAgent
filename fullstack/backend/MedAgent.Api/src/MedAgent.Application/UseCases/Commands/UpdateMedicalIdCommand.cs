using MediatR;
using MedAgent.Application.DTOs.MedicalId;
using MedAgent.Domain.Interfaces;
using MedAgent.Domain.Entities;

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
        dto.Allergies ??= new List<AllergyDto>();
        dto.ChronicConditions ??= new List<ChronicConditionDto>();
        dto.Prescriptions ??= new List<PrescriptionDto>();
        dto.EmergencyContacts ??= new List<EmergencyContactDto>();
        dto.Insurance ??= new InsuranceDto();

        var user = await _userRepository.GetByIdAsync(request.UserId);
        if (user == null) throw new KeyNotFoundException("User not found.");

        user.FirstName = dto.FirstName;
        user.LastName = dto.LastName;
        user.BloodType = dto.BloodType;
        user.Gender = dto.Gender;

        if (dto.ProfileImageId.HasValue)
            user.ProfileImageId = dto.ProfileImageId;

        user.Weight = dto.Weight;
        user.Height = dto.Height;
        user.NationalId = dto.NationalId;
        user.OrganDonor = dto.OrganDonor;
        user.AdvanceDirectives = dto.AdvanceDirectives;
        user.UpdatedAt = DateTime.UtcNow;

        var newAllergies = dto.Allergies
            .Select(a => new Allergy { UserId = user.Id, Name = a.Name, Severity = a.Severity })
            .ToList();

        var newConditions = dto.ChronicConditions
            .Select(c => new ChronicCondition { UserId = user.Id, Name = c.Name, Description = c.Description })
            .ToList();

        var newPrescriptions = dto.Prescriptions
            .Select(p => new Prescription { UserId = user.Id, Name = p.Name, Freq = p.Freq, Time = p.Time })
            .ToList();

        var newContacts = dto.EmergencyContacts
            .Select(c => new EmergencyContact
            {
                UserId = user.Id,
                Name = c.Name,
                Phone = c.Phone,
                Relation = c.Relation,
                AvatarUrl = c.Avatar,
                Type = c.Type
            })
            .ToList();

        var insuranceData = new InsuranceData
        {
            UserId = user.Id,
            ProviderName = dto.Insurance.ProviderName,
            MemberId = dto.Insurance.MemberId,
            GroupNumber = dto.Insurance.GroupNumber,
            PlanType = dto.Insurance.PlanType,
            CardImageUrl = dto.Insurance.CardImage
        };

        await _userRepository.SaveMedicalUpdateAsync(
            user, newAllergies, newConditions, newPrescriptions, newContacts, insuranceData);

        return true;
    }
}

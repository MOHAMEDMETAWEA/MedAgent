using MediatR;
using MedAgent.Application.DTOs.MedicalId;
using MedAgent.Domain.Interfaces;
using System.Linq;

namespace MedAgent.Application.UseCases.Queries;

public record GetMedicalIdQuery(Guid UserId) : IRequest<MedicalIdDto>;

public class GetMedicalIdQueryHandler : IRequestHandler<GetMedicalIdQuery, MedicalIdDto>
{
    private readonly IUserRepository _userRepository;

    public GetMedicalIdQueryHandler(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    public async Task<MedicalIdDto> Handle(GetMedicalIdQuery request, CancellationToken cancellationToken)
    {
        var user = await _userRepository.GetByIdAsync(request.UserId);
        if (user == null) throw new KeyNotFoundException("User not found.");

        return new MedicalIdDto
        {
            FirstName = user.FirstName,
            LastName = user.LastName,
            Email = user.Email,
            PatientId = user.PatientId,
            BloodType = user.BloodType,
            Gender = user.Gender,
            ProfileImageId = user.ProfileImageId,
            Weight = user.Weight,
            Height = user.Height,
            NationalId = user.NationalId,
            OrganDonor = user.OrganDonor,
            AdvanceDirectives = user.AdvanceDirectives,
            
            // Map collections
            Allergies = user.Allergies.Select(a => new AllergyDto 
            { 
                Name = a.Name, 
                Severity = a.Severity 
            }).ToList(),

            ChronicConditions = user.ChronicConditions.Select(c => new ChronicConditionDto 
            { 
                Name = c.Name, 
                Description = c.Description 
            }).ToList(),

            Prescriptions = user.Prescriptions.Select(p => new PrescriptionDto 
            { 
                Name = p.Name, 
                Freq = p.Freq, 
                Time = p.Time 
            }).ToList(),

            Insurance = user.Insurance != null ? new InsuranceDto
            {
                ProviderName = user.Insurance.ProviderName,
                MemberId = user.Insurance.MemberId,
                GroupNumber = user.Insurance.GroupNumber,
                PlanType = user.Insurance.PlanType,
                CardImage = user.Insurance.CardImageUrl
            } : new InsuranceDto(),

            EmergencyContacts = user.EmergencyContacts.Select(e => new EmergencyContactDto
            {
                Id = e.Id,
                Name = e.Name,
                Phone = e.Phone,
                Relation = e.Relation,
                Avatar = e.AvatarUrl,
                Type = e.Type
            }).ToList()
        };
    }
}

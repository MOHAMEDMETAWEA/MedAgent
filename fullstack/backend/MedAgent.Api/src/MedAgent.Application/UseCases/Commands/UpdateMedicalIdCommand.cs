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
        var user = await _userRepository.GetByIdAsync(request.UserId);
        if (user == null) throw new KeyNotFoundException("User not found.");

        // Update User Metadata
        user.FirstName = request.Dto.FirstName;
        user.LastName = request.Dto.LastName;
        user.BloodType = request.Dto.BloodType;
        user.Gender = request.Dto.Gender;
        
        if (request.Dto.ProfileImageId.HasValue) 
        {
            user.ProfileImageId = request.Dto.ProfileImageId;
        }
        
        user.Weight = request.Dto.Weight;
        user.Height = request.Dto.Height;
        user.NationalId = request.Dto.NationalId;
        user.OrganDonor = request.Dto.OrganDonor;
        user.AdvanceDirectives = request.Dto.AdvanceDirectives;
        
        // Update Collections (Allergies, Conditions, Prescriptions) - Only if provided to prevent accidental wipes during partial updates
        if (request.Dto.Allergies != null && request.Dto.Allergies.Any())
        {
            user.Allergies.Clear();
            foreach (var a in request.Dto.Allergies)
            {
                user.Allergies.Add(new Allergy { UserId = user.Id, Name = a.Name, Severity = a.Severity });
            }
        }

        if (request.Dto.ChronicConditions != null && request.Dto.ChronicConditions.Any())
        {
            user.ChronicConditions.Clear();
            foreach (var c in request.Dto.ChronicConditions)
            {
                user.ChronicConditions.Add(new ChronicCondition { UserId = user.Id, Name = c.Name, Description = c.Description });
            }
        }

        if (request.Dto.Prescriptions != null && request.Dto.Prescriptions.Any())
        {
            user.Prescriptions.Clear();
            foreach (var p in request.Dto.Prescriptions)
            {
                user.Prescriptions.Add(new Prescription { UserId = user.Id, Name = p.Name, Freq = p.Freq, Time = p.Time });
            }
        }

        // Update Insurance
        if (user.Insurance == null)
        {
            user.Insurance = new InsuranceData { UserId = user.Id };
        }
        user.Insurance.ProviderName = request.Dto.Insurance.ProviderName;
        user.Insurance.MemberId = request.Dto.Insurance.MemberId;
        user.Insurance.GroupNumber = request.Dto.Insurance.GroupNumber;
        user.Insurance.PlanType = request.Dto.Insurance.PlanType;
        user.Insurance.CardImageUrl = request.Dto.Insurance.CardImage;

        // Update Emergency Contacts (Replacement approach for simplicity/safety in batch)
        user.EmergencyContacts.Clear();
        foreach (var contactDto in request.Dto.EmergencyContacts)
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

using MediatR;
using MedAgent.Application.DTOs;
using MedAgent.Domain.Interfaces;

namespace MedAgent.Application.UseCases.Queries;

// Query
public record GetUserProfileQuery(Guid UserId) : IRequest<UserProfileDto>;

// Handler  
public class GetUserProfileQueryHandler : IRequestHandler<GetUserProfileQuery, UserProfileDto>
{
    private readonly IUserRepository _userRepository;

    public GetUserProfileQueryHandler(IUserRepository userRepository)
    {
        _userRepository = userRepository;
    }

    public async Task<UserProfileDto> Handle(GetUserProfileQuery request, CancellationToken cancellationToken)
    {
        var user = await _userRepository.GetByIdAsync(request.UserId);
        if (user == null)
        {
            throw new KeyNotFoundException("User not found.");
        }

        return new UserProfileDto
        {
            Id = user.Id,
            PatientId = user.PatientId,
            FirstName = user.FirstName,
            LastName = user.LastName,
            Email = user.Email,
            ProfileImageId = user.Photos?.FirstOrDefault(p => p.Category == "Profile")?.Id,
            BloodType = user.BloodType,
            Gender = user.Gender,
            DateOfBirth = user.DateOfBirth,
            CreatedAt = user.CreatedAt,
            UpdatedAt = user.UpdatedAt
        };
    }
}

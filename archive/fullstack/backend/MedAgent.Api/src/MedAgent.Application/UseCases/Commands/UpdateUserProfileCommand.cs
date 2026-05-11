using MediatR;
using MedAgent.Application.DTOs;
using MedAgent.Domain.Interfaces;
using MedAgent.Domain.Entities;

namespace MedAgent.Application.UseCases.Commands;

// Command
public record UpdateUserProfileCommand(Guid UserId, UpdateUserProfileDto Dto) : IRequest<UserProfileDto>;

// Handler
public class UpdateUserProfileCommandHandler : IRequestHandler<UpdateUserProfileCommand, UserProfileDto>
{
    private readonly IUserRepository _userRepository;
    private readonly IPhotoRepository _photoRepository;

    public UpdateUserProfileCommandHandler(IUserRepository userRepository, IPhotoRepository photoRepository)
    {
        _userRepository = userRepository;
        _photoRepository = photoRepository;
    }

    public async Task<UserProfileDto> Handle(UpdateUserProfileCommand request, CancellationToken cancellationToken)
    {
        var user = await _userRepository.GetByIdAsync(request.UserId);
        if (user == null)
        {
            throw new KeyNotFoundException("User not found.");
        }

        // Apply partial updates
        if (request.Dto.FirstName != null) user.FirstName = request.Dto.FirstName.Trim();
        if (request.Dto.LastName != null) user.LastName = request.Dto.LastName.Trim();
        if (request.Dto.BloodType != null) user.BloodType = request.Dto.BloodType;
        if (request.Dto.Gender != null) user.Gender = request.Dto.Gender;
        if (request.Dto.DateOfBirth.HasValue) user.DateOfBirth = request.Dto.DateOfBirth;

        Guid? profileImageId = null;

        // Process profile image if provided
        if (!string.IsNullOrEmpty(request.Dto.ProfileImage))
        {
            try 
            {
                var base64 = request.Dto.ProfileImage.Contains(",") ? request.Dto.ProfileImage.Split(',')[1] : request.Dto.ProfileImage;
                var bytes = Convert.FromBase64String(base64);
                
                var photo = new UserPhoto
                {
                    UserId = user.Id,
                    Bytes = bytes,
                    Category = "Profile",
                    ContentType = "image/jpeg",
                    FileName = "profile_updated.jpg"
                };
                
                var createdPhoto = await _photoRepository.AddAsync(photo);
                profileImageId = createdPhoto.Id;
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Photo update failed: {ex.Message}");
            }
        }
        else
        {
            // Get existing profile photo ID
            profileImageId = user.Photos?.FirstOrDefault(p => p.Category == "Profile")?.Id;
        }

        user.UpdatedAt = DateTime.UtcNow;
        var updatedUser = await _userRepository.UpdateAsync(user);

        return new UserProfileDto
        {
            Id = updatedUser.Id,
            PatientId = updatedUser.PatientId,
            FirstName = updatedUser.FirstName,
            LastName = updatedUser.LastName,
            Email = updatedUser.Email,
            ProfileImageId = profileImageId,
            BloodType = updatedUser.BloodType,
            Gender = updatedUser.Gender,
            DateOfBirth = updatedUser.DateOfBirth,
            CreatedAt = updatedUser.CreatedAt,
            UpdatedAt = updatedUser.UpdatedAt
        };
    }
}

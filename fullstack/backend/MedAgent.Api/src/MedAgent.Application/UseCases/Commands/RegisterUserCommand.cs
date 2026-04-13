using MediatR;
using MedAgent.Application.DTOs;
using MedAgent.Application.Interfaces;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;

namespace MedAgent.Application.UseCases.Commands;

// Command
public record RegisterUserCommand(RegisterUserDto Dto) : IRequest<AuthResponseDto>;

// Handler
public class RegisterUserCommandHandler : IRequestHandler<RegisterUserCommand, AuthResponseDto>
{
    private readonly IUserRepository _userRepository;
    private readonly IAuthService _authService;
    private readonly IPhotoRepository _photoRepository;

    public RegisterUserCommandHandler(IUserRepository userRepository, IAuthService authService, IPhotoRepository photoRepository)
    {
        _userRepository = userRepository;
        _authService = authService;
        _photoRepository = photoRepository;
    }

    public async Task<AuthResponseDto> Handle(RegisterUserCommand request, CancellationToken cancellationToken)
    {
        var dto = request.Dto;

        // Check if email already exists
        if (await _userRepository.EmailExistsAsync(dto.Email))
        {
            throw new ApplicationException("A user with this email already exists.");
        }

        // Create user entity
        var user = new User
        {
            FirstName = dto.FirstName.Trim(),
            LastName = dto.LastName.Trim(),
            Email = dto.Email.Trim().ToLowerInvariant(),
            PasswordHash = _authService.HashPassword(dto.Password),
            BloodType = dto.BloodType,
            Gender = dto.Gender,
            DateOfBirth = dto.DateOfBirth,
        };

        var createdUser = await _userRepository.CreateAsync(user);

        // Handle profile photo if provided
        Guid? profileImageId = null;
        if (!string.IsNullOrEmpty(dto.ProfileImage))
        {
            try 
            {
                var base64 = dto.ProfileImage.Contains(",") ? dto.ProfileImage.Split(',')[1] : dto.ProfileImage;
                var bytes = Convert.FromBase64String(base64);
                
                var photo = new UserPhoto
                {
                    UserId = createdUser.Id,
                    Bytes = bytes,
                    Category = "Profile",
                    ContentType = "image/jpeg",
                    FileName = "profile.jpg"
                };
                
                var createdPhoto = await _photoRepository.AddAsync(photo);
                profileImageId = createdPhoto.Id;
                createdUser.ProfileImageId = profileImageId;
                await _userRepository.UpdateAsync(createdUser);
            }
            catch (Exception ex)
            {
                // Log error but don't fail registration just because of a bad photo string
                // In a real app, use a logger
                Console.WriteLine($"Photo upload failed: {ex.Message}");
            }
        }

        var token = _authService.GenerateJwtToken(createdUser);

        return new AuthResponseDto
        {
            Token = token,
            User = MapToProfile(createdUser, profileImageId)
        };
    }

    private static UserProfileDto MapToProfile(User user, Guid? profileImageId) => new()
    {
        Id = user.Id,
        PatientId = user.PatientId,
        FirstName = user.FirstName,
        LastName = user.LastName,
        Email = user.Email,
        ProfileImageId = profileImageId,
        BloodType = user.BloodType,
        Gender = user.Gender,
        DateOfBirth = user.DateOfBirth,
        CreatedAt = user.CreatedAt,
        UpdatedAt = user.UpdatedAt
    };
}

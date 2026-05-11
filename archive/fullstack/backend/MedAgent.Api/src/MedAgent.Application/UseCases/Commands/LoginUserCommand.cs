using MediatR;
using MedAgent.Application.DTOs;
using MedAgent.Application.Interfaces;
using MedAgent.Domain.Interfaces;

namespace MedAgent.Application.UseCases.Commands;

// Command
public record LoginUserCommand(LoginUserDto Dto) : IRequest<AuthResponseDto>;

// Handler
public class LoginUserCommandHandler : IRequestHandler<LoginUserCommand, AuthResponseDto>
{
    private readonly IUserRepository _userRepository;
    private readonly IAuthService _authService;

    public LoginUserCommandHandler(IUserRepository userRepository, IAuthService authService)
    {
        _userRepository = userRepository;
        _authService = authService;
    }

    public async Task<AuthResponseDto> Handle(LoginUserCommand request, CancellationToken cancellationToken)
    {
        var dto = request.Dto;
        var user = await _userRepository.GetByEmailAsync(dto.Email.Trim().ToLowerInvariant());

        if (user == null || !_authService.VerifyPassword(dto.Password, user.PasswordHash))
        {
            throw new UnauthorizedAccessException("Invalid email or password.");
        }

        var token = _authService.GenerateJwtToken(user);

        return new AuthResponseDto
        {
            Token = token,
            User = new UserProfileDto
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
            }
        };
    }
}

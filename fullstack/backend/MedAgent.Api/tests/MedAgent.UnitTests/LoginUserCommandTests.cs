using MedAgent.Application.DTOs;
using MedAgent.Application.Interfaces;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;
using Moq;

namespace MedAgent.UnitTests;

public class LoginUserCommandTests
{
    private readonly Mock<IUserRepository> _userRepoMock;
    private readonly Mock<IAuthService> _authServiceMock;
    private readonly LoginUserCommandHandler _handler;

    public LoginUserCommandTests()
    {
        _userRepoMock = new Mock<IUserRepository>();
        _authServiceMock = new Mock<IAuthService>();
        _handler = new LoginUserCommandHandler(_userRepoMock.Object, _authServiceMock.Object);
    }

    [Fact]
    public async Task Handle_ValidCredentials_ReturnsToken()
    {
        // Arrange
        var user = new User
        {
            Id = Guid.NewGuid(),
            FirstName = "John",
            LastName = "Doe",
            Email = "john@example.com",
            PasswordHash = "hashed_password",
            PatientId = "#MED-123-456"
        };

        _userRepoMock.Setup(r => r.GetByEmailAsync("john@example.com"))
            .ReturnsAsync(user);

        _authServiceMock.Setup(a => a.VerifyPassword("Password1!", "hashed_password"))
            .Returns(true);

        _authServiceMock.Setup(a => a.GenerateJwtToken(user))
            .Returns("valid_jwt_token");

        var dto = new LoginUserDto { Email = "john@example.com", Password = "Password1!" };

        // Act
        var result = await _handler.Handle(new LoginUserCommand(dto), CancellationToken.None);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("valid_jwt_token", result.Token);
        Assert.Equal("John", result.User.FirstName);
    }

    [Fact]
    public async Task Handle_InvalidPassword_ThrowsUnauthorized()
    {
        // Arrange
        var user = new User
        {
            Email = "john@example.com",
            PasswordHash = "hashed_password"
        };

        _userRepoMock.Setup(r => r.GetByEmailAsync("john@example.com"))
            .ReturnsAsync(user);

        _authServiceMock.Setup(a => a.VerifyPassword("wrong_password", "hashed_password"))
            .Returns(false);

        var dto = new LoginUserDto { Email = "john@example.com", Password = "wrong_password" };

        // Act & Assert
        await Assert.ThrowsAsync<UnauthorizedAccessException>(
            () => _handler.Handle(new LoginUserCommand(dto), CancellationToken.None));
    }

    [Fact]
    public async Task Handle_UserNotFound_ThrowsUnauthorized()
    {
        // Arrange
        _userRepoMock.Setup(r => r.GetByEmailAsync(It.IsAny<string>()))
            .ReturnsAsync((User?)null);

        var dto = new LoginUserDto { Email = "nonexistent@example.com", Password = "Password1!" };

        // Act & Assert
        await Assert.ThrowsAsync<UnauthorizedAccessException>(
            () => _handler.Handle(new LoginUserCommand(dto), CancellationToken.None));
    }
}

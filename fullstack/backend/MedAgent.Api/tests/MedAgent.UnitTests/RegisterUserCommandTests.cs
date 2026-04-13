using MedAgent.Application.DTOs;
using MedAgent.Application.Interfaces;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;
using Moq;

namespace MedAgent.UnitTests;

public class RegisterUserCommandTests
{
    private readonly Mock<IUserRepository> _userRepoMock;
    private readonly Mock<IAuthService> _authServiceMock;
    private readonly Mock<IPhotoRepository> _photoRepoMock;
    private readonly RegisterUserCommandHandler _handler;

    public RegisterUserCommandTests()
    {
        _userRepoMock = new Mock<IUserRepository>();
        _authServiceMock = new Mock<IAuthService>();
        _photoRepoMock = new Mock<IPhotoRepository>();
        _handler = new RegisterUserCommandHandler(_userRepoMock.Object, _authServiceMock.Object, _photoRepoMock.Object);
    }

    [Fact]
    public async Task Handle_ValidUser_ReturnsAuthResponse()
    {
        // Arrange
        var dto = new RegisterUserDto
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john@example.com",
            Password = "Password1!",
            BloodType = "O+",
            Gender = "M"
        };

        _userRepoMock.Setup(r => r.EmailExistsAsync(It.IsAny<string>()))
            .ReturnsAsync(false);

        _authServiceMock.Setup(a => a.HashPassword(It.IsAny<string>()))
            .Returns("hashed_password");

        _userRepoMock.Setup(r => r.CreateAsync(It.IsAny<User>()))
            .ReturnsAsync((User u) => u);

        _authServiceMock.Setup(a => a.GenerateJwtToken(It.IsAny<User>()))
            .Returns("mock_jwt_token");

        // Act
        var result = await _handler.Handle(new RegisterUserCommand(dto), CancellationToken.None);

        // Assert
        Assert.NotNull(result);
        Assert.Equal("mock_jwt_token", result.Token);
        Assert.Equal("john@example.com", result.User.Email);
        Assert.Equal("John", result.User.FirstName);
    }

    [Fact]
    public async Task Handle_DuplicateEmail_ThrowsApplicationException()
    {
        // Arrange
        var dto = new RegisterUserDto
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "existing@example.com",
            Password = "Password1!"
        };

        _userRepoMock.Setup(r => r.EmailExistsAsync(It.IsAny<string>()))
            .ReturnsAsync(true);

        // Act & Assert
        await Assert.ThrowsAsync<ApplicationException>(
            () => _handler.Handle(new RegisterUserCommand(dto), CancellationToken.None));
    }

    [Fact]
    public async Task Handle_PasswordIsHashed_NotStoredPlaintext()
    {
        // Arrange
        var dto = new RegisterUserDto
        {
            FirstName = "Jane",
            LastName = "Doe",
            Email = "jane@example.com",
            Password = "MySecure1!",
        };

        User? capturedUser = null;

        _userRepoMock.Setup(r => r.EmailExistsAsync(It.IsAny<string>()))
            .ReturnsAsync(false);

        _authServiceMock.Setup(a => a.HashPassword("MySecure1!"))
            .Returns("bcrypt_hashed_value");

        _userRepoMock.Setup(r => r.CreateAsync(It.IsAny<User>()))
            .Callback<User>(u => capturedUser = u)
            .ReturnsAsync((User u) => u);

        _authServiceMock.Setup(a => a.GenerateJwtToken(It.IsAny<User>()))
            .Returns("token");

        // Act
        await _handler.Handle(new RegisterUserCommand(dto), CancellationToken.None);

        // Assert
        Assert.NotNull(capturedUser);
        Assert.Equal("bcrypt_hashed_value", capturedUser!.PasswordHash);
        Assert.NotEqual("MySecure1!", capturedUser.PasswordHash);
    }
}

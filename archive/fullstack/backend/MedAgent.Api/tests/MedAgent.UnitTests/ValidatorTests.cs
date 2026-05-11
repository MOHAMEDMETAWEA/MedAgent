using FluentValidation.TestHelper;
using MedAgent.Application.DTOs;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Application.Validators;

namespace MedAgent.UnitTests;

public class ValidatorTests
{
    private readonly RegisterUserValidator _registerValidator = new();
    private readonly LoginUserValidator _loginValidator = new();
    private readonly UpdateUserProfileValidator _updateValidator = new();

    // ─── Registration Validation ─────────────────────────────────────────

    [Fact]
    public void Register_ValidData_PassesValidation()
    {
        var command = new RegisterUserCommand(new RegisterUserDto
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john@example.com",
            Password = "Password1!",
            BloodType = "O+",
            Gender = "M"
        });

        var result = _registerValidator.TestValidate(command);
        result.ShouldNotHaveAnyValidationErrors();
    }

    [Fact]
    public void Register_EmptyFirstName_FailsValidation()
    {
        var command = new RegisterUserCommand(new RegisterUserDto
        {
            FirstName = "",
            LastName = "Doe",
            Email = "john@example.com",
            Password = "Password1!"
        });

        var result = _registerValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.FirstName);
    }

    [Fact]
    public void Register_WeakPassword_NoUppercase_Fails()
    {
        var command = new RegisterUserCommand(new RegisterUserDto
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john@example.com",
            Password = "password1!"
        });

        var result = _registerValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.Password);
    }

    [Fact]
    public void Register_WeakPassword_NoNumber_Fails()
    {
        var command = new RegisterUserCommand(new RegisterUserDto
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john@example.com",
            Password = "Password!"
        });

        var result = _registerValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.Password);
    }

    [Fact]
    public void Register_WeakPassword_NoSpecialChar_Fails()
    {
        var command = new RegisterUserCommand(new RegisterUserDto
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john@example.com",
            Password = "Password1"
        });

        var result = _registerValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.Password);
    }

    [Fact]
    public void Register_InvalidEmail_FailsValidation()
    {
        var command = new RegisterUserCommand(new RegisterUserDto
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "not-an-email",
            Password = "Password1!"
        });

        var result = _registerValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.Email);
    }

    [Fact]
    public void Register_InvalidBloodType_Fails()
    {
        var command = new RegisterUserCommand(new RegisterUserDto
        {
            FirstName = "John",
            LastName = "Doe",
            Email = "john@example.com",
            Password = "Password1!",
            BloodType = "Z+"
        });

        var result = _registerValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.BloodType);
    }

    // ─── Login Validation ────────────────────────────────────────────────

    [Fact]
    public void Login_EmptyEmail_Fails()
    {
        var command = new LoginUserCommand(new LoginUserDto { Email = "", Password = "pass" });
        var result = _loginValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.Email);
    }

    [Fact]
    public void Login_EmptyPassword_Fails()
    {
        var command = new LoginUserCommand(new LoginUserDto { Email = "a@b.com", Password = "" });
        var result = _loginValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.Password);
    }

    // ─── Update Profile Validation ───────────────────────────────────────

    [Fact]
    public void Update_InvalidGender_Fails()
    {
        var command = new UpdateUserProfileCommand(Guid.NewGuid(), new UpdateUserProfileDto { Gender = "X" });
        var result = _updateValidator.TestValidate(command);
        result.ShouldHaveValidationErrorFor(x => x.Dto.Gender);
    }

    [Fact]
    public void Update_ValidGender_Passes()
    {
        var command = new UpdateUserProfileCommand(Guid.NewGuid(), new UpdateUserProfileDto { Gender = "F" });
        var result = _updateValidator.TestValidate(command);
        result.ShouldNotHaveValidationErrorFor(x => x.Dto.Gender);
    }
}

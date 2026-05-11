using FluentValidation;
using MedAgent.Application.UseCases.Commands;

namespace MedAgent.Application.Validators;

public class UpdateUserProfileValidator : AbstractValidator<UpdateUserProfileCommand>
{
    private static readonly string[] ValidBloodTypes = 
        { "Unknown", "O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-" };

    public UpdateUserProfileValidator()
    {
        RuleFor(x => x.Dto.FirstName)
            .MaximumLength(100).WithMessage("First name must not exceed 100 characters.")
            .When(x => x.Dto.FirstName != null);

        RuleFor(x => x.Dto.LastName)
            .MaximumLength(100).WithMessage("Last name must not exceed 100 characters.")
            .When(x => x.Dto.LastName != null);

        RuleFor(x => x.Dto.BloodType)
            .Must(bt => ValidBloodTypes.Contains(bt!))
            .WithMessage("Invalid blood type.")
            .When(x => x.Dto.BloodType != null);

        RuleFor(x => x.Dto.Gender)
            .Must(g => g == "M" || g == "F")
            .WithMessage("Gender must be 'M' or 'F'.")
            .When(x => x.Dto.Gender != null);
    }
}

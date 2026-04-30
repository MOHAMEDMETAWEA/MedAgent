using FluentValidation;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Application.DTOs.MedicalId;
using System.Linq;

namespace MedAgent.Application.Validators;

public sealed class UpdateMedicalIdCommandValidator : AbstractValidator<UpdateMedicalIdCommand>
{
    public UpdateMedicalIdCommandValidator()
    {
        RuleFor(x => x.UserId).NotEmpty();
        RuleFor(x => x.Dto).NotNull().SetValidator(new MedicalIdDtoValidator());
    }

    private sealed class MedicalIdDtoValidator : AbstractValidator<MedicalIdDto>
    {
        public MedicalIdDtoValidator()
        {
            RuleFor(x => x.FirstName).NotEmpty().MaximumLength(100);
            RuleFor(x => x.LastName).NotEmpty().MaximumLength(100);
            RuleFor(x => x.Email).NotEmpty().EmailAddress();

            // JSON may send explicit null for lists; RuleForEach on null throws inside FluentValidation → 500.
            RuleForEach(x => x.EmergencyContacts ?? Enumerable.Empty<EmergencyContactDto>()).ChildRules(contact =>
            {
                contact.RuleFor(c => c.Name).NotEmpty();
                contact.RuleFor(c => c.Phone).NotEmpty();
            });

            RuleFor(x => x.Insurance).NotNull();
        }
    }
}


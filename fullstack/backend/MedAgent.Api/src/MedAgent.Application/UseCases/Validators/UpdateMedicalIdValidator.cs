using FluentValidation;
using MedAgent.Application.DTOs.MedicalId;

namespace MedAgent.Application.UseCases.Validators;

public class UpdateMedicalIdValidator : AbstractValidator<MedicalIdDto>
{
    public UpdateMedicalIdValidator()
    {
        RuleFor(x => x.FirstName).NotEmpty().MaximumLength(100);
        RuleFor(x => x.LastName).NotEmpty().MaximumLength(100);
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        
        RuleForEach(x => x.EmergencyContacts).ChildRules(contact => 
        {
            contact.RuleFor(c => c.Name).NotEmpty();
            contact.RuleFor(c => c.Phone).NotEmpty();
        });

        RuleFor(x => x.Insurance).SetValidator(new InsuranceValidator());
    }
}

public class InsuranceValidator : AbstractValidator<InsuranceDto>
{
    public InsuranceValidator()
    {
        // Add specific rules for insurance fields if necessary
    }
}

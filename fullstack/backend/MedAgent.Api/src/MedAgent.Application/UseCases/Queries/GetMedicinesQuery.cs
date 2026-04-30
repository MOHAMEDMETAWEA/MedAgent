using MediatR;
using MedAgent.Application.DTOs;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Domain.Interfaces;

namespace MedAgent.Application.UseCases.Queries;

public record GetMedicinesQuery(Guid UserId) : IRequest<IReadOnlyList<MedicineDto>>;

public class GetMedicinesQueryHandler : IRequestHandler<GetMedicinesQuery, IReadOnlyList<MedicineDto>>
{
    private readonly IMedicineRepository _repo;
    public GetMedicinesQueryHandler(IMedicineRepository repo) => _repo = repo;

    public async Task<IReadOnlyList<MedicineDto>> Handle(GetMedicinesQuery request, CancellationToken ct)
    {
        var medicines = await _repo.GetAllByUserIdAsync(request.UserId);
        return medicines.Select(AddMedicineCommandHandler.ToDto).ToList();
    }
}

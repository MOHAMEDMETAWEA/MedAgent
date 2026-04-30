using MediatR;
using MedAgent.Application.DTOs;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;

namespace MedAgent.Application.UseCases.Commands;

// ── Add ──────────────────────────────────────────────────────────────────────
public record AddMedicineCommand(Guid UserId, MedicineDto Dto) : IRequest<MedicineDto>;

public class AddMedicineCommandHandler : IRequestHandler<AddMedicineCommand, MedicineDto>
{
    private readonly IMedicineRepository _repo;
    public AddMedicineCommandHandler(IMedicineRepository repo) => _repo = repo;

    public async Task<MedicineDto> Handle(AddMedicineCommand request, CancellationToken ct)
    {
        var m = new Medicine
        {
            UserId = request.UserId,
            Name = request.Dto.Name,
            Dosage = request.Dto.Dosage,
            Desc = request.Dto.Desc,
            Type = request.Dto.Type,
            Freq = request.Dto.Freq,
            Time = request.Dto.Time,
            Supply = request.Dto.Supply,
            Status = request.Dto.Status,
            Archived = request.Dto.Archived,
            Category = request.Dto.Category
        };
        await _repo.AddAsync(m);
        return ToDto(m);
    }

    internal static MedicineDto ToDto(Medicine m) => new()
    {
        Id = m.Id,
        Name = m.Name,
        Dosage = m.Dosage,
        Desc = m.Desc,
        Type = m.Type,
        Freq = m.Freq,
        Time = m.Time,
        Supply = m.Supply,
        Status = m.Status,
        Archived = m.Archived,
        Category = m.Category
    };
}

// ── Update ────────────────────────────────────────────────────────────────────
public record UpdateMedicineCommand(Guid UserId, Guid MedicineId, MedicineDto Dto) : IRequest<MedicineDto?>;

public class UpdateMedicineCommandHandler : IRequestHandler<UpdateMedicineCommand, MedicineDto?>
{
    private readonly IMedicineRepository _repo;
    public UpdateMedicineCommandHandler(IMedicineRepository repo) => _repo = repo;

    public async Task<MedicineDto?> Handle(UpdateMedicineCommand request, CancellationToken ct)
    {
        var m = await _repo.GetByIdAsync(request.MedicineId, request.UserId);
        if (m == null) return null;

        m.Name = request.Dto.Name;
        m.Dosage = request.Dto.Dosage;
        m.Desc = request.Dto.Desc;
        m.Type = request.Dto.Type;
        m.Freq = request.Dto.Freq;
        m.Time = request.Dto.Time;
        m.Supply = request.Dto.Supply;
        m.Status = request.Dto.Status;
        m.Archived = request.Dto.Archived;
        m.Category = request.Dto.Category;

        await _repo.UpdateAsync(m);
        return AddMedicineCommandHandler.ToDto(m);
    }
}

// ── Delete ────────────────────────────────────────────────────────────────────
public record DeleteMedicineCommand(Guid UserId, Guid MedicineId) : IRequest<bool>;

public class DeleteMedicineCommandHandler : IRequestHandler<DeleteMedicineCommand, bool>
{
    private readonly IMedicineRepository _repo;
    public DeleteMedicineCommandHandler(IMedicineRepository repo) => _repo = repo;

    public async Task<bool> Handle(DeleteMedicineCommand request, CancellationToken ct) =>
        await _repo.DeleteAsync(request.MedicineId, request.UserId);
}

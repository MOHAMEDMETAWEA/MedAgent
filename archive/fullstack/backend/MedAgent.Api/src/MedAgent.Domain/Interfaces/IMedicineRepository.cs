using MedAgent.Domain.Entities;
namespace MedAgent.Domain.Interfaces;

public interface IMedicineRepository
{
    Task<IReadOnlyList<Medicine>> GetAllByUserIdAsync(Guid userId);
    Task<Medicine?> GetByIdAsync(Guid id, Guid userId);
    Task<Medicine> AddAsync(Medicine medicine);
    Task<Medicine> UpdateAsync(Medicine medicine);
    Task<bool> DeleteAsync(Guid id, Guid userId);
}

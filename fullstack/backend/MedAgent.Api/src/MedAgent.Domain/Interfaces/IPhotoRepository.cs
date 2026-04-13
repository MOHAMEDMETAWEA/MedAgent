using MedAgent.Domain.Entities;

namespace MedAgent.Domain.Interfaces;

public interface IPhotoRepository
{
    Task<UserPhoto?> GetByIdAsync(Guid id);
    Task<IEnumerable<UserPhoto>> GetByUserIdAsync(Guid userId, string? category = null);
    Task<UserPhoto> AddAsync(UserPhoto photo);
    Task<bool> DeleteAsync(Guid id);
}

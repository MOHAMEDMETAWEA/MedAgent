using MedAgent.Domain.Entities;

namespace MedAgent.Domain.Interfaces;

public interface IUserRepository
{
    Task<User?> GetByIdAsync(Guid id);
    /// <summary>User with medical-id graph only (excludes Photos) to avoid EF concurrency issues on SaveChanges.</summary>
    Task<User?> GetByIdForMedicalUpdateAsync(Guid id);
    Task<User?> GetByEmailAsync(string email);
    Task<User> CreateAsync(User user);
    Task<User> UpdateAsync(User user);
    Task<bool> DeleteAsync(Guid id);
    Task<bool> EmailExistsAsync(string email);
}

using MedAgent.Domain.Entities;

namespace MedAgent.Domain.Interfaces;

public interface IUserRepository
{
    Task<User?> GetByIdAsync(Guid id);
    Task<User?> GetByIdForMedicalUpdateAsync(Guid id);
    Task<User?> GetByEmailAsync(string email);
    Task<User> CreateAsync(User user);
    Task<User> UpdateAsync(User user);
    Task<bool> DeleteAsync(Guid id);
    Task<bool> EmailExistsAsync(string email);

    /// <summary>
    /// Atomically replaces all medical collections for a user and saves scalar changes.
    /// Uses ExecuteDeleteAsync to bypass EF change tracking, preventing DbUpdateConcurrencyException
    /// that occurs with the Clear() + Add() pattern on tracked SQLite collections.
    /// </summary>
    Task SaveMedicalUpdateAsync(
        User user,
        IReadOnlyList<Allergy> allergies,
        IReadOnlyList<ChronicCondition> conditions,
        IReadOnlyList<Prescription> prescriptions,
        IReadOnlyList<EmergencyContact> contacts,
        InsuranceData insuranceData);
}

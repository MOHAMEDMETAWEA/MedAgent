using Microsoft.EntityFrameworkCore;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;
using MedAgent.Infrastructure.Data;

namespace MedAgent.Infrastructure.Repositories;

public class UserRepository : IUserRepository
{
    private readonly AppDbContext _context;

    public UserRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<User?> GetByIdAsync(Guid id)
    {
        return await _context.Users
            .Include(u => u.Photos)
            .Include(u => u.EmergencyContacts)
            .Include(u => u.Insurance)
            .Include(u => u.Allergies)
            .Include(u => u.ChronicConditions)
            .Include(u => u.Prescriptions)
            .FirstOrDefaultAsync(u => u.Id == id);
    }

    public async Task<User?> GetByIdForMedicalUpdateAsync(Guid id)
    {
        return await _context.Users
            .Include(u => u.EmergencyContacts)
            .Include(u => u.Insurance)
            .Include(u => u.Allergies)
            .Include(u => u.ChronicConditions)
            .Include(u => u.Prescriptions)
            .FirstOrDefaultAsync(u => u.Id == id);
    }

    public async Task<User?> GetByEmailAsync(string email)
    {
        return await _context.Users
            .Include(u => u.Photos)
            .Include(u => u.EmergencyContacts)
            .Include(u => u.Insurance)
            .Include(u => u.Allergies)
            .Include(u => u.ChronicConditions)
            .Include(u => u.Prescriptions)
            .FirstOrDefaultAsync(u => u.Email == email.ToLowerInvariant());
    }

    public async Task<User> CreateAsync(User user)
    {
        _context.Users.Add(user);
        await _context.SaveChangesAsync();
        return user;
    }

    public async Task<User> UpdateAsync(User user)
    {
        var entry = _context.Entry(user);
        if (entry.State == EntityState.Detached)
            _context.Users.Update(user);

        await _context.SaveChangesAsync();
        return user;
    }

    public async Task SaveMedicalUpdateAsync(
        User user,
        IReadOnlyList<Allergy> allergies,
        IReadOnlyList<ChronicCondition> conditions,
        IReadOnlyList<Prescription> prescriptions,
        IReadOnlyList<EmergencyContact> contacts,
        InsuranceData insuranceData)
    {
        // Delete all existing collection rows directly via SQL — bypasses EF change tracking
        // entirely, which is the root cause of DbUpdateConcurrencyException with the old
        // Clear() + Add() pattern on SQLite-tracked collections.
        await _context.Allergies.Where(a => a.UserId == user.Id).ExecuteDeleteAsync();
        await _context.ChronicConditions.Where(c => c.UserId == user.Id).ExecuteDeleteAsync();
        await _context.Prescriptions.Where(p => p.UserId == user.Id).ExecuteDeleteAsync();
        await _context.EmergencyContacts.Where(e => e.UserId == user.Id).ExecuteDeleteAsync();

        if (allergies.Count > 0) _context.Allergies.AddRange(allergies);
        if (conditions.Count > 0) _context.ChronicConditions.AddRange(conditions);
        if (prescriptions.Count > 0) _context.Prescriptions.AddRange(prescriptions);
        if (contacts.Count > 0) _context.EmergencyContacts.AddRange(contacts);

        var existing = await _context.InsuranceDatas
            .FirstOrDefaultAsync(i => i.UserId == user.Id);

        if (existing == null)
        {
            _context.InsuranceDatas.Add(insuranceData);
        }
        else
        {
            existing.ProviderName = insuranceData.ProviderName;
            existing.MemberId = insuranceData.MemberId;
            existing.GroupNumber = insuranceData.GroupNumber;
            existing.PlanType = insuranceData.PlanType;
            existing.CardImageUrl = insuranceData.CardImageUrl;
        }

        var entry = _context.Entry(user);
        if (entry.State == EntityState.Detached)
            _context.Users.Update(user);

        await _context.SaveChangesAsync();
    }

    public async Task<bool> DeleteAsync(Guid id)
    {
        var user = await _context.Users.FindAsync(id);
        if (user == null) return false;

        _context.Users.Remove(user);
        await _context.SaveChangesAsync();
        return true;
    }

    public async Task<bool> EmailExistsAsync(string email)
    {
        return await _context.Users
            .AnyAsync(u => u.Email == email.ToLowerInvariant());
    }
}

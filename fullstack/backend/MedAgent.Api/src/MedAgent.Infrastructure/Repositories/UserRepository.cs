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
        // Never call DbSet.Update() on an entity that is already tracked with Includes.
        // That re-attaches the whole graph and commonly breaks collection relationships on SaveChanges.
        var entry = _context.Entry(user);
        if (entry.State == EntityState.Detached)
            _context.Users.Update(user);

        await _context.SaveChangesAsync();
        return user;
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

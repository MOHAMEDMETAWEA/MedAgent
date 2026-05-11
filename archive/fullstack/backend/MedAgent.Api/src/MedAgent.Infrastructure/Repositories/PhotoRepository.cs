using Microsoft.EntityFrameworkCore;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;
using MedAgent.Infrastructure.Data;

namespace MedAgent.Infrastructure.Repositories;

public class PhotoRepository : IPhotoRepository
{
    private readonly AppDbContext _context;

    public PhotoRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<UserPhoto?> GetByIdAsync(Guid id)
    {
        return await _context.UserPhotos.FindAsync(id);
    }

    public async Task<IEnumerable<UserPhoto>> GetByUserIdAsync(Guid userId, string? category = null)
    {
        var query = _context.UserPhotos.Where(p => p.UserId == userId);
        
        if (!string.IsNullOrEmpty(category))
        {
            query = query.Where(p => p.Category == category);
        }

        return await query.OrderByDescending(p => p.CreatedAt).ToListAsync();
    }

    public async Task<UserPhoto> AddAsync(UserPhoto photo)
    {
        _context.UserPhotos.Add(photo);
        await _context.SaveChangesAsync();
        return photo;
    }

    public async Task<bool> DeleteAsync(Guid id)
    {
        var photo = await _context.UserPhotos.FindAsync(id);
        if (photo == null) return false;

        _context.UserPhotos.Remove(photo);
        await _context.SaveChangesAsync();
        return true;
    }
}

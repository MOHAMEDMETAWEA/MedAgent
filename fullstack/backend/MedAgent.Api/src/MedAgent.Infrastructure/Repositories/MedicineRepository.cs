using Microsoft.EntityFrameworkCore;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;
using MedAgent.Infrastructure.Data;

namespace MedAgent.Infrastructure.Repositories;

public class MedicineRepository : IMedicineRepository
{
    private readonly AppDbContext _context;
    public MedicineRepository(AppDbContext context) => _context = context;

    public async Task<IReadOnlyList<Medicine>> GetAllByUserIdAsync(Guid userId) =>
        await _context.Medicines.Where(m => m.UserId == userId).OrderBy(m => m.CreatedAt).ToListAsync();

    public async Task<Medicine?> GetByIdAsync(Guid id, Guid userId) =>
        await _context.Medicines.FirstOrDefaultAsync(m => m.Id == id && m.UserId == userId);

    public async Task<Medicine> AddAsync(Medicine medicine)
    {
        _context.Medicines.Add(medicine);
        await _context.SaveChangesAsync();
        return medicine;
    }

    public async Task<Medicine> UpdateAsync(Medicine medicine)
    {
        _context.Medicines.Update(medicine);
        await _context.SaveChangesAsync();
        return medicine;
    }

    public async Task<bool> DeleteAsync(Guid id, Guid userId)
    {
        var m = await _context.Medicines.FirstOrDefaultAsync(m => m.Id == id && m.UserId == userId);
        if (m == null) return false;
        _context.Medicines.Remove(m);
        await _context.SaveChangesAsync();
        return true;
    }
}

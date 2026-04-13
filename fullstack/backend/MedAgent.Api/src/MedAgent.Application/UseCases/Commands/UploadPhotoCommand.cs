using MediatR;
using MedAgent.Application.DTOs;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;

namespace MedAgent.Application.UseCases.Commands;

public record UploadPhotoCommand(
    Guid UserId, 
    string? Base64Data, // Can be null if using IFormFile (handled in API)
    byte[]? BinaryData,
    string ContentType,
    string Category,
    string FileName) : IRequest<PhotoDto>;

public class UploadPhotoCommandHandler : IRequestHandler<UploadPhotoCommand, PhotoDto>
{
    private readonly IPhotoRepository _photoRepository;

    public UploadPhotoCommandHandler(IPhotoRepository photoRepository)
    {
        _photoRepository = photoRepository;
    }

    public async Task<PhotoDto> Handle(UploadPhotoCommand request, CancellationToken cancellationToken)
    {
        byte[] bytes;

        if (request.BinaryData != null)
        {
            bytes = request.BinaryData;
        }
        else if (!string.IsNullOrEmpty(request.Base64Data))
        {
            // Remove data:image/jpeg;base64, if present
            var base64 = request.Base64Data.Contains(",") 
                ? request.Base64Data.Split(',')[1] 
                : request.Base64Data;
            
            bytes = Convert.FromBase64String(base64);
        }
        else
        {
            throw new ArgumentException("No photo data provided.");
        }

        if (bytes.Length > 5 * 1024 * 1024) // 5MB limit
        {
            throw new ArgumentException("Photo size exceeds 5MB limit.");
        }

        var photo = new UserPhoto
        {
            UserId = request.UserId,
            Bytes = bytes,
            ContentType = request.ContentType,
            Category = request.Category,
            FileName = request.FileName,
            CreatedAt = DateTime.UtcNow
        };

        var createdPhoto = await _photoRepository.AddAsync(photo);

        return new PhotoDto
        {
            Id = createdPhoto.Id,
            Category = createdPhoto.Category,
            FileName = createdPhoto.FileName,
            ContentType = createdPhoto.ContentType,
            CreatedAt = createdPhoto.CreatedAt
        };
    }
}

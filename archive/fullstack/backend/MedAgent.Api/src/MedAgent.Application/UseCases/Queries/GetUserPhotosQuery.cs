using MediatR;
using MedAgent.Application.DTOs;
using MedAgent.Domain.Interfaces;

namespace MedAgent.Application.UseCases.Queries;

public record GetUserPhotosQuery(Guid UserId, string? Category = null) : IRequest<IEnumerable<PhotoDto>>;

public class GetUserPhotosQueryHandler : IRequestHandler<GetUserPhotosQuery, IEnumerable<PhotoDto>>
{
    private readonly IPhotoRepository _photoRepository;

    public GetUserPhotosQueryHandler(IPhotoRepository photoRepository)
    {
        _photoRepository = photoRepository;
    }

    public async Task<IEnumerable<PhotoDto>> Handle(GetUserPhotosQuery request, CancellationToken cancellationToken)
    {
        var photos = await _photoRepository.GetByUserIdAsync(request.UserId, request.Category);

        return photos.Select(p => new PhotoDto
        {
            Id = p.Id,
            Category = p.Category,
            FileName = p.FileName,
            ContentType = p.ContentType,
            CreatedAt = p.CreatedAt
        });
    }
}

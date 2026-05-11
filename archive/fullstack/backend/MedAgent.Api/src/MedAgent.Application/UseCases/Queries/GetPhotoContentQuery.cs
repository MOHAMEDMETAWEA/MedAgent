using MediatR;
using MedAgent.Domain.Entities;
using MedAgent.Domain.Interfaces;

namespace MedAgent.Application.UseCases.Queries;

public record GetPhotoContentQuery(Guid PhotoId) : IRequest<UserPhoto?>;

public class GetPhotoContentQueryHandler : IRequestHandler<GetPhotoContentQuery, UserPhoto?>
{
    private readonly IPhotoRepository _photoRepository;

    public GetPhotoContentQueryHandler(IPhotoRepository photoRepository)
    {
        _photoRepository = photoRepository;
    }

    public async Task<UserPhoto?> Handle(GetPhotoContentQuery request, CancellationToken cancellationToken)
    {
        return await _photoRepository.GetByIdAsync(request.PhotoId);
    }
}

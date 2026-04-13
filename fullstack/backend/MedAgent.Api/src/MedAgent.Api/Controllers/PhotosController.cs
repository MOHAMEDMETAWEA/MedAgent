using System.Security.Claims;
using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Application.UseCases.Queries;

namespace MedAgent.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
[Authorize]
public class PhotosController : ControllerBase
{
    private readonly IMediator _mediator;

    public PhotosController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Upload a new photo. Supports multipart form data.
    /// </summary>
    [HttpPost]
    [ProducesResponseType(StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    public async Task<IActionResult> UploadPhoto([FromForm] IFormFile file, [FromForm] string category = "General")
    {
        if (file == null || file.Length == 0)
            return BadRequest("No file uploaded.");

        using var ms = new MemoryStream();
        await file.CopyToAsync(ms);
        var bytes = ms.ToArray();

        var userId = GetCurrentUserId();
        var command = new UploadPhotoCommand(
            UserId: userId,
            Base64Data: null,
            BinaryData: bytes,
            ContentType: file.ContentType,
            Category: category,
            FileName: file.FileName
        );

        var result = await _mediator.Send(command);
        return CreatedAtAction(nameof(GetPhotoContent), new { id = result.Id }, result);
    }

    /// <summary>
    /// Get all photo metadata for the current user.
    /// </summary>
    [HttpGet("me")]
    public async Task<IActionResult> GetMyPhotos([FromQuery] string? category)
    {
        var userId = GetCurrentUserId();
        var result = await _mediator.Send(new GetUserPhotosQuery(userId, category));
        return Ok(result);
    }

    /// <summary>
    /// Stream the actual photo binary content.
    /// Accessible via <img> tags.
    /// </summary>
    [HttpGet("content/{id}")]
    [AllowAnonymous] // Allow <img> tags to load images without header if needed, or keep protected if sensitive
    public async Task<IActionResult> GetPhotoContent(Guid id)
    {
        var photo = await _mediator.Send(new GetPhotoContentQuery(id));
        
        if (photo == null)
            return NotFound();

        return File(photo.Bytes, photo.ContentType);
    }

    private Guid GetCurrentUserId()
    {
        var userIdClaim = User.FindFirst(ClaimTypes.NameIdentifier)?.Value
            ?? User.FindFirst("sub")?.Value;

        if (string.IsNullOrEmpty(userIdClaim) || !Guid.TryParse(userIdClaim, out var userId))
        {
            throw new UnauthorizedAccessException("Invalid user token.");
        }

        return userId;
    }
}

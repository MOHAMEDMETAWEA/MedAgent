using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using MedAgent.Application.DTOs.MedicalId;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Application.UseCases.Queries;
using System.Security.Claims;

namespace MedAgent.Api.Controllers;

[Authorize]
[ApiController]
[Route("api/medical-id")]
public class MedicalIdController : ControllerBase
{
    private readonly IMediator _mediator;

    public MedicalIdController(IMediator mediator)
    {
        _mediator = mediator;
    }

    [HttpGet]
    public async Task<ActionResult<MedicalIdDto>> Get()
    {
        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (string.IsNullOrEmpty(userIdString)) return Unauthorized();

        var query = new GetMedicalIdQuery(Guid.Parse(userIdString));
        var result = await _mediator.Send(query);
        return Ok(result);
    }

    [HttpPut]
    public async Task<IActionResult> Update([FromBody] MedicalIdDto dto)
    {
        var userIdString = User.FindFirstValue(ClaimTypes.NameIdentifier);
        if (string.IsNullOrEmpty(userIdString)) return Unauthorized();

        var command = new UpdateMedicalIdCommand(Guid.Parse(userIdString), dto);
        await _mediator.Send(command);
        return NoContent();
    }
}

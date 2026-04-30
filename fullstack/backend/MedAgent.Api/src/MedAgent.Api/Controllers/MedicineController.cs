using MediatR;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using MedAgent.Application.DTOs;
using MedAgent.Application.UseCases.Commands;
using MedAgent.Application.UseCases.Queries;
using System.Security.Claims;

namespace MedAgent.Api.Controllers;

[Authorize]
[ApiController]
[Route("api/medicines")]
public class MedicineController : ControllerBase
{
    private readonly IMediator _mediator;
    public MedicineController(IMediator mediator) => _mediator = mediator;

    private Guid? CurrentUserId()
    {
        var s = User.FindFirstValue(ClaimTypes.NameIdentifier);
        return Guid.TryParse(s, out var id) ? id : null;
    }

    [HttpGet]
    public async Task<IActionResult> GetAll()
    {
        var userId = CurrentUserId();
        if (userId == null) return Unauthorized();
        var result = await _mediator.Send(new GetMedicinesQuery(userId.Value));
        return Ok(result);
    }

    [HttpPost]
    public async Task<IActionResult> Add([FromBody] MedicineDto dto)
    {
        var userId = CurrentUserId();
        if (userId == null) return Unauthorized();
        var result = await _mediator.Send(new AddMedicineCommand(userId.Value, dto));
        return CreatedAtAction(nameof(GetAll), result);
    }

    [HttpPut("{id:guid}")]
    public async Task<IActionResult> Update(Guid id, [FromBody] MedicineDto dto)
    {
        var userId = CurrentUserId();
        if (userId == null) return Unauthorized();
        var result = await _mediator.Send(new UpdateMedicineCommand(userId.Value, id, dto));
        if (result == null) return NotFound();
        return Ok(result);
    }

    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> Delete(Guid id)
    {
        var userId = CurrentUserId();
        if (userId == null) return Unauthorized();
        var deleted = await _mediator.Send(new DeleteMedicineCommand(userId.Value, id));
        if (!deleted) return NotFound();
        return NoContent();
    }
}

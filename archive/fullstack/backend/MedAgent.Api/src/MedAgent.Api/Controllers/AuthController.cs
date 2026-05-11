using MediatR;
using Microsoft.AspNetCore.Mvc;
using MedAgent.Application.DTOs;
using MedAgent.Application.UseCases.Commands;

namespace MedAgent.Api.Controllers;

[ApiController]
[Route("api/[controller]")]
public class AuthController : ControllerBase
{
    private readonly IMediator _mediator;

    public AuthController(IMediator mediator)
    {
        _mediator = mediator;
    }

    /// <summary>
    /// Register a new user account.
    /// </summary>
    [HttpPost("register")]
    [ProducesResponseType(typeof(AuthResponseDto), StatusCodes.Status201Created)]
    [ProducesResponseType(StatusCodes.Status400BadRequest)]
    [ProducesResponseType(StatusCodes.Status409Conflict)]
    public async Task<IActionResult> Register([FromBody] RegisterUserDto dto)
    {
        var result = await _mediator.Send(new RegisterUserCommand(dto));
        return CreatedAtAction(nameof(Register), result);
    }

    /// <summary>
    /// Authenticate an existing user and receive a JWT token.
    /// </summary>
    [HttpPost("login")]
    [ProducesResponseType(typeof(AuthResponseDto), StatusCodes.Status200OK)]
    [ProducesResponseType(StatusCodes.Status401Unauthorized)]
    public async Task<IActionResult> Login([FromBody] LoginUserDto dto)
    {
        var result = await _mediator.Send(new LoginUserCommand(dto));
        return Ok(result);
    }
}

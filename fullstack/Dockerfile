# ============================================================
# Stage 1: Build the Vite.js Frontend
# ============================================================
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies first (utilizes Docker layer cache)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --silent

# Copy source and build
COPY frontend/ ./
RUN npm run build


# ============================================================
# Stage 2: Build the .NET Backend
# ============================================================
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS backend-build

WORKDIR /app/backend

# Copy solution and project files first (utilizes Docker layer cache)
COPY backend/MedAgent.Api/MedAgent.sln ./
COPY backend/MedAgent.Api/src/MedAgent.Domain/MedAgent.Domain.csproj ./src/MedAgent.Domain/
COPY backend/MedAgent.Api/src/MedAgent.Application/MedAgent.Application.csproj ./src/MedAgent.Application/
COPY backend/MedAgent.Api/src/MedAgent.Infrastructure/MedAgent.Infrastructure.csproj ./src/MedAgent.Infrastructure/
COPY backend/MedAgent.Api/src/MedAgent.Api/MedAgent.Api.csproj ./src/MedAgent.Api/
COPY backend/MedAgent.Api/tests/MedAgent.UnitTests/MedAgent.UnitTests.csproj ./tests/MedAgent.UnitTests/

# Restore NuGet packages
RUN dotnet restore

# Copy full source code and publish
COPY backend/MedAgent.Api/ ./
RUN dotnet publish src/MedAgent.Api/MedAgent.Api.csproj -c Release -o /app/publish --no-restore


# ============================================================
# Stage 3: Final Runtime Image
# ============================================================
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime

WORKDIR /app

# Copy published backend
COPY --from=backend-build /app/publish ./

# Copy frontend build output into wwwroot (served as static files)
COPY --from=frontend-build /app/frontend/dist ./wwwroot

# Create directory for SQLite database persistence
RUN mkdir -p /app/data

# Set environment variables
ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

EXPOSE 8080

ENTRYPOINT ["dotnet", "MedAgent.Api.dll"]

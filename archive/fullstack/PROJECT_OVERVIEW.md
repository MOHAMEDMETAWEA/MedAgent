# MedAgent — Project Overview & Architecture Guide

Welcome to **MedAgent**, an AI-powered medical assistant designed to provide real-time SOS support, manage Medical IDs, and facilitate secure insurance sharing.

---

## 🏗️ Architecture Philosophy

MedAgent is built with a strictly decoupled **Frontend (React/Vite)** and **Backend (.NET 8 API)** architecture. Consistency, type safety, and clean separation of concerns are the core pillars of the project.

### 🌐 Frontend (React + Tailwind 4)
The frontend follows a **Feature-Based** structure to ensure scalability and ease of navigation.

- **Design System**: All styling is driven by tokens. 
    - **Theme Rules**: NEVER use hardcoded colors or spacing. All brand tokens reside in `src/theme/theme.css` and `src/theme/tokens.js`.
    - **Micro-interactions**: Use `Framer Motion` for all interactive elements (buttons, cards, modals). All interactive components should inherit motion variants from `theme`.
- **Localization (i18n)**: 
    - **Rule**: Direct text strings in components are forbidden. 
    - **Usage**: Use the `useTranslation` hook. Adding a new language or updating text must be done in `src/i18n/locales/ar.json` and `en.json`.
- **API Interaction**: 
    - **Rule**: All requests MUST go through `src/services/apiClient.js`. 
    - **Reasoning**: This handles centralized base URL configuration, JWT Bearer token injection, and global `401 Unauthorized` handling.

### ⚙️ Backend (.NET 8 Clean Architecture)
The backend follows the **Clean Architecture** pattern to isolate business logic from infrastructure.

- **Layers Implementation**:
    - **API Layer**: Controllers are kept "thin." They only delegate work to MediatR.
    - **Application Layer**: Contains `MediatR` Commands/Queries, DTOs, and Validators.
    - **Domain Layer**: Contains Entities and Core interfaces. No external dependencies.
    - **Infrastructure Layer**: Implementation of Repositories, DB Context (SQLite), and external services (Auth).
- **Coding Standards**:
    - **Immutability**: All Commands, Queries, and DTOs should be C# `record` types.
    - **Naming**: Async methods must have the `Async` suffix (e.g., `GetByIdAsync`).
    - **Validation**: Strict use of `FluentValidation` before any handler execution.

---

## 🗺️ Project Directory Map (AI-Ready)

*To help developers and AI models navigate quickly without exploring every folder:*

```bash
root/
├── backend/
│   ├── src/
│   │   ├── MedAgent.Api/           # Startup, Controllers, Middleware
│   │   ├── MedAgent.Application/   # UseCases (Commands/Queries), DTOs, Validators
│   │   ├── MedAgent.Domain/        # Entities, Repository Interfaces
│   │   └── MedAgent.Infrastructure/# EntityFramework, SQLite, Repositories
│   └── tests/                      # Unit & Integration Tests (xUnit)
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── ui/                 # Reusable atomic molecules (Buttons, Inputs)
    │   │   └── {feature}/          # Feature-specific components (SOS, Chat, Medical)
    │   ├── i18n/                   # Arabic & English translation files
    │   ├── theme/                  # Tailwind 4 configuration and tokens
    │   ├── services/               # API clients and data transformers
    │   └── pages/                  # Top-level route components
```

---

## 🤖 AI Onboarding Cheat Sheet

If you are an AI model working on this project, follow this checklist to ensure consistency:

1.  **Adding a Feature**:
    - Create the Backend Command/Query and DTO in `MedAgent.Application`.
    - Add a Validator in `MedAgent.Application/Validators`.
    - Implement the logic in the Handler.
    - Expose via a thin Controller in `MedAgent.Api`.
    - In Frontend, add the service call in `src/services/api/`.
    - Add UI strings to `src/i18n/locales/` (Both AR and EN).
2.  **Modifying Styles**:
    - Check `src/theme/theme.css` before adding any new utility class.
    - Use `var(--color-...)` for colors.
3.  **Security**:
    - Ensure all API calls use the centralized `apiClient`.
    - Use `ProtectedRoute.jsx` for private frontend routes.

---

## 🧪 Testing & Quality
- **Backend**: Primary tests are in `backend/MedAgent.Api/tests/MedAgent.UnitTests`. Run using `dotnet test`.
- **Frontend**: Component logic should be documented using JSDoc to assist IntelliSense and AI models.

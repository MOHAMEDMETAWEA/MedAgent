# 🛡️ MedAgent: Your AI Medical Companion

MedAgent is a cutting-edge medical assistance platform that bridges the gap between emergency response and personal health management. Combining real-time SOS capabilities, a secure Medical ID, and smart insurance sharing, MedAgent ensures you are never alone in a medical crisis.

## Environment & Configurations
Ensure the `.env` file in the frontend is properly connected:
```
VITE_API_BASE_URL=http://localhost:10000
VITE_AI_ENGINE_BASE_URL=http://localhost:8000
```
This is essential for `apiClient.js` (C# connections) and `aiService.js` (Python connections) to function together seamlessly, powered by a unified JWT token!

---

## ✨ Key Features

- **🚨 Intelligent SOS System**: One-tap emergency alerts with real-time geolocation and automated SMS dispatch to emergency contacts.
- **🆔 Digital Medical ID**: A centralized vault for your blood type, allergies, medications, and chronic conditions—accessible instantly by first responders.
- **📄 Secure Insurance Sharing**: Scan, store, and share your insurance details via functional QR codes or secure links.
- **💬 AI Health Assistant**: An interactive chat interface to answer medical queries and guide you through first-aid protocols.
- **🌍 Multi-lingual Support**: Seamless localization for Arabic and English with RTL/LTR layout adjustment.

---

## 🏗️ Architecture & Documentation

This project follows a professional **Clean Architecture** for the backend and a **Feature-Driven** React setup for the frontend.

For a deep dive into the engineering rules, directory structure, and contribution guidelines, please refer to:
👉 **[PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md)** (Essential for Developers & AI Models)

---

## 🚀 Getting Started

### Prerequisites
- **Node.js 20+** (Frontend)
- **.NET 8 SDK** (Backend)
- **Docker** (Optional, for containerized deployment)

### Local Development

#### 1. Clone the repository
```bash
git clone https://github.com/ahmsaied/NewMedAgent.git
cd NewMedAgent
```

#### 2. Setup the Backend
```bash
cd backend/MedAgent.Api
dotnet restore
dotnet run --project src/MedAgent.Api
```
The API will be available at `http://localhost:10000` (or the port specified in your env). Swagger documentation is available at `/swagger`.

#### 3. Setup the Frontend
```bash
cd frontend
npm install
npm run dev
```
The app will be available at `http://localhost:5173`.

---

## 🐳 Docker Deployment

To run the entire stack using Docker:

```bash
docker-compose up --build
```
This builds both the .NET API and the Vite frontend, serving the latter as static files through the backend. Access the app at `http://localhost:8080`.

---

## 🛠️ Tech Stack

- **Frontend**: React 19, Vite, Tailwind CSS 4, Framer Motion, Axios, i18next.
- **Backend**: .NET 8, Entity Framework Core, SQLite, MediatR, FluentValidation.
- **Security**: JWT Authentication, CORS protection, Secure Password Hashing.

---

## 👨‍💻 Contributing

We follow strict Clean Code principles. Before contributing, please read the **[Architecture Guide](./PROJECT_OVERVIEW.md)** carefully. 

- Use **MediatR** for all business logic in the backend.
- Use **i18n** for all frontend strings.
- Ensure all interactive UI components use **Framer Motion**.

---

## 📄 License

This project is licensed under the MIT License.

# KooAI Frontend

Modern web interface for KooAI simulation post-processing system.

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Material-UI (MUI)** - UI components
- **React Router** - Routing
- **TanStack Query (React Query)** - Server state management
- **Axios** - HTTP client
- **Zustand** - Client state management (optional)
- **Three.js + React Three Fiber** - 3D visualization
- **Recharts** - Charts and graphs

## Prerequisites

- Node.js >= 18
- npm or yarn

## Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

Update `.env` with your backend API URL:

```env
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## Build for Production

```bash
npm run build
```

The production build will be in the `dist/` directory.

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and hooks
│   │   ├── client.ts     # Axios configuration
│   │   ├── simulations.ts # API methods
│   │   └── hooks.ts      # React Query hooks
│   ├── components/       # Reusable components
│   ├── layouts/          # Layout components
│   │   └── MainLayout.tsx
│   ├── pages/            # Page components
│   │   ├── UploadPage.tsx
│   │   ├── SimulationsListPage.tsx
│   │   └── SimulationDetailPage.tsx
│   ├── store/            # State management
│   ├── types/            # TypeScript types
│   │   └── simulation.ts
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── .env                  # Environment variables
├── package.json
├── tsconfig.json
└── vite.config.ts
```

## Features

### Current Features

- ✅ Simulation file upload (CSV, VTK)
- ✅ Simulations list view
- ✅ Simulation detail view
- ✅ Responsive design
- ✅ Material-UI components
- ✅ API integration with backend

### Coming Soon

- 🔨 3D visualization (Three.js)
- 🔨 Interactive charts (Recharts)
- 🔨 Field analysis tools
- 🔨 Convergence plots
- 🔨 Spatial analysis
- 🔨 Real-time updates
- 🔨 User authentication

## API Integration

The frontend communicates with the KooAI backend API:

- **Base URL**: `http://localhost:8000` (configurable via env)
- **Endpoints**:
  - `POST /api/simulations/upload` - Upload simulation file
  - `GET /api/simulations` - List simulations
  - `GET /api/simulations/{id}` - Get simulation details
  - `DELETE /api/simulations/{id}` - Delete simulation
  - `POST /api/simulations/{id}/analyze` - Analyze field
  - `POST /api/simulations/{id}/compare` - Compare timesteps
  - `POST /api/simulations/{id}/convergence` - Compute convergence
  - `POST /api/simulations/{id}/spatial` - Spatial analysis

## Development

### Code Style

The project uses ESLint and TypeScript for code quality:

```bash
npm run lint
```

### Type Checking

```bash
npm run type-check
```

## Deployment

### Docker

Build the frontend with Docker:

```bash
docker build -t kooai-frontend .
docker run -p 5173:80 kooai-frontend
```

### Nginx

For production deployment, build the app and serve with Nginx:

```bash
npm run build
# Copy dist/ contents to your web server
```

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test locally before committing
4. Write meaningful commit messages

## License

[MIT License](LICENSE)

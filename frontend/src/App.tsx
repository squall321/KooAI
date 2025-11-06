/**
 * Main App component with routing
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { MainLayout } from './layouts/MainLayout';
import { UploadPage } from './pages/UploadPage';
import { SimulationsListPage } from './pages/SimulationsListPage';
import { SimulationDetailPage } from './pages/SimulationDetailPage';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Create MUI theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<MainLayout />}>
              <Route index element={<Navigate to="/simulations" replace />} />
              <Route path="upload" element={<UploadPage />} />
              <Route path="simulations" element={<SimulationsListPage />} />
              <Route path="simulations/:id" element={<SimulationDetailPage />} />
              <Route path="visualization" element={<div>Visualization Page - Coming Soon</div>} />
              <Route path="*" element={<Navigate to="/simulations" replace />} />
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;

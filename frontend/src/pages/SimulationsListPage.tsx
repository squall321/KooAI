/**
 * Simulations list page
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  CardActionArea,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
} from '@mui/material';
import DeleteIcon from '@mui/icons-material/Delete';
import { useSimulations, useDeleteSimulation } from '../api/hooks';
import { format } from 'date-fns';

export const SimulationsListPage: React.FC = () => {
  const { data, isLoading, isError, error } = useSimulations();
  const deleteMutation = useDeleteSimulation();
  const navigate = useNavigate();

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this simulation?')) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (isError) {
    return (
      <Alert severity="error">
        {error instanceof Error ? error.message : 'Failed to load simulations'}
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Simulations
      </Typography>

      {data && data.simulations.length === 0 && (
        <Alert severity="info" sx={{ mt: 3 }}>
          No simulations found. Upload your first simulation to get started!
        </Alert>
      )}

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' }, gap: 3, mt: 2 }}>
        {data?.simulations.map((sim) => (
          <Box key={sim.simulation_id}>
            <Card>
              <CardActionArea
                onClick={() => navigate(`/simulations/${sim.simulation_id}`)}
              >
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="start">
                    <Typography variant="h6" component="div" gutterBottom>
                      {sim.name}
                    </Typography>
                    <IconButton
                      size="small"
                      onClick={(e) => handleDelete(e, sim.simulation_id)}
                      disabled={deleteMutation.isPending}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>

                  <Chip
                    label={sim.simulation_type}
                    size="small"
                    color="primary"
                    sx={{ mb: 1 }}
                  />

                  <Typography variant="body2" color="text.secondary">
                    Timesteps: {sim.num_timesteps}
                  </Typography>

                  <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                    Created: {format(new Date(sim.created_at), 'PPp')}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          </Box>
        ))}
      </Box>
    </Box>
  );
};

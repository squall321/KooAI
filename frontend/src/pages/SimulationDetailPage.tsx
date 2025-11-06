/**
 * Simulation detail page
 */

import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  Divider,
  Tabs,
  Tab,
} from '@mui/material';
import { useSimulation } from '../api/hooks';
import { MeshViewer3D } from '../components/visualization/MeshViewer3D';
import { FieldAnalysisPanel } from '../components/analysis/FieldAnalysisPanel';
import { ConvergenceAnalysisPanel } from '../components/analysis/ConvergenceAnalysisPanel';

export const SimulationDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: simulation, isLoading, isError, error } = useSimulation(id!);
  const [activeTab, setActiveTab] = useState(0);

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
        {error instanceof Error ? error.message : 'Failed to load simulation'}
      </Alert>
    );
  }

  if (!simulation) {
    return <Alert severity="warning">Simulation not found</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {simulation.name}
      </Typography>

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)' }, gap: 3 }}>
        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                General Information
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Type
                  </Typography>
                  <Chip label={simulation.simulation_type} size="small" color="primary" />
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Simulation ID
                  </Typography>
                  <Typography variant="body1">{simulation.simulation_id}</Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Number of Timesteps
                  </Typography>
                  <Typography variant="body1">{simulation.num_timesteps}</Typography>
                </Box>

                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Time Range
                  </Typography>
                  <Typography variant="body1">
                    {simulation.time_range[0].toFixed(4)} - {simulation.time_range[1].toFixed(4)}
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Mesh Information
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    Vertices
                  </Typography>
                  <Typography variant="body1">
                    {simulation.mesh_info.num_vertices.toLocaleString()}
                  </Typography>
                </Box>

                {simulation.mesh_info.num_cells !== undefined && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Cells
                    </Typography>
                    <Typography variant="body1">
                      {simulation.mesh_info.num_cells.toLocaleString()}
                    </Typography>
                  </Box>
                )}

                {simulation.mesh_info.num_faces !== undefined && (
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Faces
                    </Typography>
                    <Typography variant="body1">
                      {simulation.mesh_info.num_faces.toLocaleString()}
                    </Typography>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ gridColumn: { xs: '1', md: 'span 2' } }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Available Fields
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {simulation.fields.map((field) => (
                  <Chip key={field} label={field} variant="outlined" />
                ))}
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ gridColumn: { xs: '1', md: 'span 2' } }}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                3D Visualization
              </Typography>
              <Divider sx={{ mb: 2 }} />

              <Box sx={{ height: 500, width: '100%' }}>
                <MeshViewer3D wireframe />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ gridColumn: { xs: '1', md: 'span 2' } }}>
          <Card>
            <Tabs
              value={activeTab}
              onChange={(_, newValue) => setActiveTab(newValue)}
              sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}
            >
              <Tab label="Field Analysis" />
              <Tab label="Convergence Analysis" />
            </Tabs>

            <CardContent>
              {activeTab === 0 && (
                <FieldAnalysisPanel
                  simulationId={simulation.simulation_id}
                  fields={simulation.fields}
                  numTimesteps={simulation.num_timesteps}
                />
              )}
              {activeTab === 1 && (
                <ConvergenceAnalysisPanel
                  simulationId={simulation.simulation_id}
                  fields={simulation.fields}
                />
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>
    </Box>
  );
};

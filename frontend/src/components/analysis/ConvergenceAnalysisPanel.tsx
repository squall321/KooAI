/**
 * Convergence Analysis Panel Component
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  MenuItem,
  Divider,
  CircularProgress,
  Alert,
} from '@mui/material';
import TimelineIcon from '@mui/icons-material/Timeline';
import { useComputeConvergence } from '../../api/hooks';
import { ConvergenceChart } from '../visualization/ConvergenceChart';
import type { ComputeConvergenceResponse } from '../../types/simulation';

interface ConvergenceAnalysisPanelProps {
  simulationId: string;
  fields: string[];
}

export const ConvergenceAnalysisPanel: React.FC<ConvergenceAnalysisPanelProps> = ({
  simulationId,
  fields,
}) => {
  const [selectedField, setSelectedField] = useState(fields[0] || '');
  const [tolerance, setTolerance] = useState(1e-6);
  const [convergenceResult, setConvergenceResult] = useState<ComputeConvergenceResponse | null>(
    null
  );

  const computeConvergenceMutation = useComputeConvergence(simulationId);

  const handleAnalyze = () => {
    if (!selectedField) return;

    computeConvergenceMutation.mutate(
      {
        field_name: selectedField,
        tolerance,
      },
      {
        onSuccess: (data) => {
          setConvergenceResult(data);
        },
      }
    );
  };

  return (
    <Box>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Convergence Analysis
        </Typography>
        <Divider sx={{ mb: 2 }} />

        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <TextField
            select
            label="Field"
            value={selectedField}
            onChange={(e) => setSelectedField(e.target.value)}
            fullWidth
          >
            {fields.map((field) => (
              <MenuItem key={field} value={field}>
                {field}
              </MenuItem>
            ))}
          </TextField>

          <TextField
            type="number"
            label="Tolerance"
            value={tolerance}
            onChange={(e) => setTolerance(parseFloat(e.target.value) || 1e-6)}
            fullWidth
            helperText="Convergence tolerance (RMS change threshold)"
            inputProps={{
              step: 1e-7,
              min: 1e-10,
            }}
          />

          <Button
            variant="contained"
            startIcon={
              computeConvergenceMutation.isPending ? <CircularProgress size={20} /> : <TimelineIcon />
            }
            onClick={handleAnalyze}
            disabled={!selectedField || computeConvergenceMutation.isPending}
            fullWidth
          >
            {computeConvergenceMutation.isPending ? 'Computing...' : 'Compute Convergence'}
          </Button>

          {computeConvergenceMutation.isError && (
            <Alert severity="error">
              {computeConvergenceMutation.error instanceof Error
                ? computeConvergenceMutation.error.message
                : 'Convergence computation failed'}
            </Alert>
          )}
        </Box>
      </Paper>

      {convergenceResult && (
        <Box sx={{ mt: 3 }}>
          <ConvergenceChart
            convergenceData={convergenceResult.convergence}
            fieldName={convergenceResult.field_name}
          />
        </Box>
      )}
    </Box>
  );
};

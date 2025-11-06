/**
 * Convergence Analysis Chart Component
 */

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { Box, Typography, Paper, Chip } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import type { ConvergenceData } from '../../types/simulation';

interface ConvergenceChartProps {
  convergenceData: ConvergenceData;
  fieldName: string;
}

export const ConvergenceChart: React.FC<ConvergenceChartProps> = ({
  convergenceData,
  fieldName,
}) => {
  const { timesteps, times, rms_changes, max_changes, is_converged, convergence_timestep } =
    convergenceData;

  // Prepare data for chart
  const data = timesteps.map((step, index) => ({
    timestep: step,
    time: times[index],
    rms_change: rms_changes[index],
    max_change: max_changes[index],
  }));

  return (
    <Paper sx={{ p: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">{fieldName} - Convergence Analysis</Typography>
        {is_converged && (
          <Chip
            icon={<CheckCircleIcon />}
            label={`Converged at step ${convergence_timestep}`}
            color="success"
            size="small"
          />
        )}
      </Box>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestep" label={{ value: 'Timestep', position: 'insideBottom', offset: -5 }} />
          <YAxis
            scale="log"
            domain={['auto', 'auto']}
            label={{ value: 'Change', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip
            formatter={(value: number) => value.toExponential(3)}
            labelFormatter={(label) => `Timestep: ${label}`}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="rms_change"
            stroke="#2196f3"
            name="RMS Change"
            strokeWidth={2}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="max_change"
            stroke="#f50057"
            name="Max Change"
            strokeWidth={2}
            dot={false}
          />
          {is_converged && convergence_timestep && (
            <ReferenceLine
              x={convergence_timestep}
              stroke="green"
              strokeDasharray="3 3"
              label="Convergence"
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          {is_converged
            ? `Field converged at timestep ${convergence_timestep}`
            : 'Field has not yet converged'}
        </Typography>
      </Box>
    </Paper>
  );
};

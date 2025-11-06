/**
 * Field Statistics Chart Component
 */

import React from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Box, Typography, Paper } from '@mui/material';
import type { FieldStatistics } from '../../types/simulation';

interface FieldStatisticsChartProps {
  statistics: FieldStatistics;
  fieldName: string;
}

export const FieldStatisticsChart: React.FC<FieldStatisticsChartProps> = ({
  statistics,
  fieldName,
}) => {
  const data = [
    { name: 'Min', value: statistics.min },
    { name: 'Mean', value: statistics.mean },
    { name: 'Max', value: statistics.max },
  ];

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        {fieldName} - Statistics
      </Typography>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="value" fill="#2196f3" />
        </BarChart>
      </ResponsiveContainer>

      <Box sx={{ mt: 2, display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 2 }}>
        <Box>
          <Typography variant="body2" color="text.secondary">
            Standard Deviation
          </Typography>
          <Typography variant="h6">{statistics.std.toExponential(3)}</Typography>
        </Box>

        {statistics.percentiles && (
          <>
            <Box>
              <Typography variant="body2" color="text.secondary">
                25th Percentile
              </Typography>
              <Typography variant="h6">
                {statistics.percentiles['25']?.toExponential(3) || 'N/A'}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                50th Percentile (Median)
              </Typography>
              <Typography variant="h6">
                {statistics.percentiles['50']?.toExponential(3) || 'N/A'}
              </Typography>
            </Box>
            <Box>
              <Typography variant="body2" color="text.secondary">
                75th Percentile
              </Typography>
              <Typography variant="h6">
                {statistics.percentiles['75']?.toExponential(3) || 'N/A'}
              </Typography>
            </Box>
          </>
        )}
      </Box>
    </Paper>
  );
};

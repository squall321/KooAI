/**
 * Field Analysis Panel Component
 */

import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Divider,
  CircularProgress,
  Alert,
} from '@mui/material';
import AnalyticsIcon from '@mui/icons-material/Analytics';
import { useAnalyzeField } from '../../api/hooks';
import { FieldStatisticsChart } from '../visualization/FieldStatisticsChart';
import type { AnalyzeFieldResponse } from '../../types/simulation';

interface FieldAnalysisPanelProps {
  simulationId: string;
  fields: string[];
  numTimesteps: number;
}

export const FieldAnalysisPanel: React.FC<FieldAnalysisPanelProps> = ({
  simulationId,
  fields,
  numTimesteps,
}) => {
  const [selectedField, setSelectedField] = useState(fields[0] || '');
  const [timestep, setTimestep] = useState(0);
  const [computeOutliers, setComputeOutliers] = useState(false);
  const [outlierThreshold, setOutlierThreshold] = useState(3.0);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeFieldResponse | null>(null);

  const analyzeFieldMutation = useAnalyzeField(simulationId);

  const handleAnalyze = () => {
    if (!selectedField) return;

    analyzeFieldMutation.mutate(
      {
        field_name: selectedField,
        timestep,
        compute_outliers: computeOutliers,
        outlier_threshold: outlierThreshold,
      },
      {
        onSuccess: (data) => {
          setAnalysisResult(data);
        },
      }
    );
  };

  return (
    <Box>
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Field Analysis
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
            label="Timestep"
            value={timestep}
            onChange={(e) => setTimestep(Math.max(0, Math.min(numTimesteps - 1, parseInt(e.target.value) || 0)))}
            fullWidth
            helperText="Select timestep to analyze"
            inputProps={{
              min: 0,
              max: numTimesteps - 1,
            }}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={computeOutliers}
                onChange={(e) => setComputeOutliers(e.target.checked)}
              />
            }
            label="Compute Outliers"
          />

          {computeOutliers && (
            <TextField
              type="number"
              label="Outlier Threshold"
              value={outlierThreshold}
              onChange={(e) => setOutlierThreshold(parseFloat(e.target.value) || 3.0)}
              fullWidth
              helperText="Number of standard deviations"
              inputProps={{
                step: 0.1,
                min: 0.1,
              }}
            />
          )}

          <Button
            variant="contained"
            startIcon={analyzeFieldMutation.isPending ? <CircularProgress size={20} /> : <AnalyticsIcon />}
            onClick={handleAnalyze}
            disabled={!selectedField || analyzeFieldMutation.isPending}
            fullWidth
          >
            {analyzeFieldMutation.isPending ? 'Analyzing...' : 'Analyze Field'}
          </Button>

          {analyzeFieldMutation.isError && (
            <Alert severity="error">
              {analyzeFieldMutation.error instanceof Error
                ? analyzeFieldMutation.error.message
                : 'Analysis failed'}
            </Alert>
          )}
        </Box>
      </Paper>

      {analysisResult && (
        <Box sx={{ mt: 3 }}>
          <FieldStatisticsChart
            statistics={analysisResult.statistics}
            fieldName={analysisResult.field_name}
          />

          {analysisResult.outliers && analysisResult.outliers.count > 0 && (
            <Paper sx={{ p: 2, mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Outliers Detected
              </Typography>
              <Typography variant="body1">
                Found {analysisResult.outliers.count} outliers
                (threshold: {analysisResult.outliers.threshold} std devs)
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Outlier indices: {analysisResult.outliers.indices.slice(0, 10).join(', ')}
                {analysisResult.outliers.indices.length > 10 && '...'}
              </Typography>
            </Paper>
          )}
        </Box>
      )}
    </Box>
  );
};

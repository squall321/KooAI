/**
 * Simulation upload page
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  TextField,
  LinearProgress,
  Alert,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { useUploadSimulation } from '../api/hooks';

export const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState('');
  const [analyze, setAnalyze] = useState(true);
  const navigate = useNavigate();

  const uploadMutation = useUploadSimulation();

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0]);
      if (!name) {
        // Auto-fill name from filename
        const filename = event.target.files[0].name;
        const nameWithoutExt = filename.replace(/\.[^/.]+$/, '');
        setName(nameWithoutExt);
      }
    }
  };

  const handleSubmit = async () => {
    if (!file) return;

    uploadMutation.mutate(
      { file, name, analyze },
      {
        onSuccess: (data) => {
          // Navigate to simulation detail page
          navigate(`/simulations/${data.simulation_info.simulation_id}`);
        },
      }
    );
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Upload Simulation
      </Typography>

      <Card sx={{ maxWidth: 800, mt: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {uploadMutation.isError && (
              <Alert severity="error">
                {uploadMutation.error instanceof Error
                  ? uploadMutation.error.message
                  : 'Upload failed. Please try again.'}
              </Alert>
            )}

            {uploadMutation.isSuccess && (
              <Alert severity="success">
                Simulation uploaded successfully!
              </Alert>
            )}

            <TextField
              label="Simulation Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              fullWidth
              helperText="Optional: Auto-filled from filename"
            />

            <Box>
              <input
                accept=".csv,.vtk"
                style={{ display: 'none' }}
                id="raised-button-file"
                type="file"
                onChange={handleFileChange}
              />
              <label htmlFor="raised-button-file">
                <Button
                  variant="contained"
                  component="span"
                  startIcon={<CloudUploadIcon />}
                >
                  Choose File
                </Button>
              </label>
              {file && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  Selected: {file.name} ({(file.size / 1024).toFixed(2)} KB)
                </Typography>
              )}
            </Box>

            <FormControlLabel
              control={
                <Checkbox
                  checked={analyze}
                  onChange={(e) => setAnalyze(e.target.checked)}
                />
              }
              label="Analyze on upload"
            />

            {uploadMutation.isPending && (
              <Box>
                <Typography variant="body2" gutterBottom>
                  Uploading...
                </Typography>
                <LinearProgress />
              </Box>
            )}

            <Button
              variant="contained"
              color="primary"
              size="large"
              onClick={handleSubmit}
              disabled={!file || uploadMutation.isPending}
            >
              Upload
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

/**
 * Simulation API methods
 */

import { apiClient } from './client';
import type {
  SimulationInfo,
  ListSimulationsResponse,
  UploadSimulationResponse,
  AnalyzeFieldResponse,
  CompareTimestepsResponse,
  ComputeConvergenceResponse,
  SpatialAnalysisResponse,
  SpatialRegion,
} from '../types/simulation';

/**
 * Upload a simulation file
 */
export const uploadSimulation = async (
  file: File,
  name?: string,
  analyze?: boolean
): Promise<UploadSimulationResponse> => {
  const formData = new FormData();
  formData.append('file', file);
  if (name) formData.append('name', name);
  if (analyze !== undefined) formData.append('analyze', String(analyze));

  const response = await apiClient.post<UploadSimulationResponse>(
    '/api/simulations/upload',
    formData,
    {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 seconds for file upload
    }
  );

  return response.data;
};

/**
 * Get simulation by ID
 */
export const getSimulation = async (id: string): Promise<SimulationInfo> => {
  const response = await apiClient.get<SimulationInfo>(`/api/simulations/${id}`);
  return response.data;
};

/**
 * List all simulations
 */
export const listSimulations = async (
  skip: number = 0,
  limit: number = 50
): Promise<ListSimulationsResponse> => {
  const response = await apiClient.get<ListSimulationsResponse>('/api/simulations', {
    params: { skip, limit },
  });
  return response.data;
};

/**
 * Delete simulation
 */
export const deleteSimulation = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/simulations/${id}`);
};

/**
 * Analyze field
 */
export const analyzeField = async (
  id: string,
  field_name: string,
  timestep: number = 0,
  compute_outliers: boolean = false,
  outlier_threshold: number = 3.0
): Promise<AnalyzeFieldResponse> => {
  const response = await apiClient.post<AnalyzeFieldResponse>(
    `/api/simulations/${id}/analyze`,
    {
      field_name,
      timestep,
      compute_outliers,
      outlier_threshold,
    }
  );
  return response.data;
};

/**
 * Compare timesteps
 */
export const compareTimesteps = async (
  id: string,
  field_name: string
): Promise<CompareTimestepsResponse> => {
  const response = await apiClient.post<CompareTimestepsResponse>(
    `/api/simulations/${id}/compare`,
    { field_name }
  );
  return response.data;
};

/**
 * Compute convergence
 */
export const computeConvergence = async (
  id: string,
  field_name: string,
  tolerance: number = 1e-6
): Promise<ComputeConvergenceResponse> => {
  const response = await apiClient.post<ComputeConvergenceResponse>(
    `/api/simulations/${id}/convergence`,
    { field_name, tolerance }
  );
  return response.data;
};

/**
 * Spatial analysis
 */
export const spatialAnalysis = async (
  id: string,
  field_name: string,
  timestep: number,
  region: SpatialRegion
): Promise<SpatialAnalysisResponse> => {
  const response = await apiClient.post<SpatialAnalysisResponse>(
    `/api/simulations/${id}/spatial`,
    {
      field_name,
      timestep,
      region,
    }
  );
  return response.data;
};

/**
 * React Query hooks for simulations
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  uploadSimulation,
  getSimulation,
  listSimulations,
  deleteSimulation,
  analyzeField,
  compareTimesteps,
  computeConvergence,
  spatialAnalysis,
} from './simulations';
import type { SpatialRegion } from '../types/simulation';

// Query keys
export const simulationKeys = {
  all: ['simulations'] as const,
  lists: () => [...simulationKeys.all, 'list'] as const,
  list: (filters?: { skip?: number; limit?: number }) =>
    [...simulationKeys.lists(), filters] as const,
  details: () => [...simulationKeys.all, 'detail'] as const,
  detail: (id: string) => [...simulationKeys.details(), id] as const,
};

/**
 * Fetch simulations list
 */
export const useSimulations = (skip: number = 0, limit: number = 50) => {
  return useQuery({
    queryKey: simulationKeys.list({ skip, limit }),
    queryFn: () => listSimulations(skip, limit),
  });
};

/**
 * Fetch single simulation
 */
export const useSimulation = (id: string) => {
  return useQuery({
    queryKey: simulationKeys.detail(id),
    queryFn: () => getSimulation(id),
    enabled: !!id,
  });
};

/**
 * Upload simulation mutation
 */
export const useUploadSimulation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      file,
      name,
      analyze,
    }: {
      file: File;
      name?: string;
      analyze?: boolean;
    }) => uploadSimulation(file, name, analyze),
    onSuccess: () => {
      // Invalidate simulations list
      queryClient.invalidateQueries({ queryKey: simulationKeys.lists() });
    },
  });
};

/**
 * Delete simulation mutation
 */
export const useDeleteSimulation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => deleteSimulation(id),
    onSuccess: (_, id) => {
      // Remove from cache
      queryClient.invalidateQueries({ queryKey: simulationKeys.lists() });
      queryClient.removeQueries({ queryKey: simulationKeys.detail(id) });
    },
  });
};

/**
 * Analyze field mutation
 */
export const useAnalyzeField = (simulationId: string) => {
  return useMutation({
    mutationFn: ({
      field_name,
      timestep = 0,
      compute_outliers = false,
      outlier_threshold = 3.0,
    }: {
      field_name: string;
      timestep?: number;
      compute_outliers?: boolean;
      outlier_threshold?: number;
    }) => analyzeField(simulationId, field_name, timestep, compute_outliers, outlier_threshold),
  });
};

/**
 * Compare timesteps mutation
 */
export const useCompareTimesteps = (simulationId: string) => {
  return useMutation({
    mutationFn: (field_name: string) => compareTimesteps(simulationId, field_name),
  });
};

/**
 * Compute convergence mutation
 */
export const useComputeConvergence = (simulationId: string) => {
  return useMutation({
    mutationFn: ({ field_name, tolerance = 1e-6 }: { field_name: string; tolerance?: number }) =>
      computeConvergence(simulationId, field_name, tolerance),
  });
};

/**
 * Spatial analysis mutation
 */
export const useSpatialAnalysis = (simulationId: string) => {
  return useMutation({
    mutationFn: ({
      field_name,
      timestep,
      region,
    }: {
      field_name: string;
      timestep: number;
      region: SpatialRegion;
    }) => spatialAnalysis(simulationId, field_name, timestep, region),
  });
};

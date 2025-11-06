/**
 * Simulation TypeScript types matching the backend API
 */

export interface SimulationInfo {
  simulation_id: string;
  name: string;
  simulation_type: string;
  num_timesteps: number;
  time_range: [number, number];
  fields: string[];
  mesh_info: {
    num_vertices: number;
    num_cells?: number;
    num_faces?: number;
    bounds?: [[number, number, number], [number, number, number]];
  };
  created_at: string;
  metadata?: Record<string, any>;
}

export interface FieldStatistics {
  min: number;
  max: number;
  mean: number;
  std: number;
  percentiles: {
    [key: string]: number;
  };
}

export interface OutlierInfo {
  indices: number[];
  values: number[];
  count: number;
  threshold: number;
}

export interface AnalyzeFieldResponse {
  field_name: string;
  timestep: number;
  time: number;
  statistics: FieldStatistics;
  outliers?: OutlierInfo;
}

export interface TimestepComparison {
  timestep: number;
  time: number;
  rms_change: number;
  max_change: number;
  relative_change: number;
}

export interface CompareTimestepsResponse {
  field_name: string;
  comparisons: TimestepComparison[];
}

export interface ConvergenceData {
  timesteps: number[];
  times: number[];
  rms_changes: number[];
  max_changes: number[];
  is_converged: boolean;
  convergence_timestep?: number;
}

export interface ComputeConvergenceResponse {
  field_name: string;
  convergence: ConvergenceData;
}

export interface SpatialRegion {
  type: 'box' | 'sphere' | 'cylinder';
  bounds?: [[number, number, number], [number, number, number]];
  center?: [number, number, number];
  radius?: number;
  height?: number;
}

export interface SpatialAnalysisResponse {
  field_name: string;
  timestep: number;
  time: number;
  region: SpatialRegion;
  statistics: FieldStatistics;
  point_count: number;
}

export interface SimulationListItem {
  simulation_id: string;
  name: string;
  simulation_type: string;
  num_timesteps: number;
  created_at: string;
}

export interface ListSimulationsResponse {
  simulations: SimulationListItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface UploadSimulationResponse {
  message: string;
  simulation_info: SimulationInfo;
}

export interface ErrorResponse {
  error: string;
  detail?: string;
}

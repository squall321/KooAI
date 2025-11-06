/**
 * 3D Mesh Viewer using Three.js and React Three Fiber
 */

import React, { useRef, useState } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { Box, IconButton, Stack, Typography } from '@mui/material';
import CenterFocusStrongIcon from '@mui/icons-material/CenterFocusStrong';
import type { Mesh } from 'three';

interface MeshViewer3DProps {
  vertices?: number[][];
  faces?: number[][];
  cells?: number[][];
  wireframe?: boolean;
}

/**
 * Mesh geometry component
 */
const MeshGeometry: React.FC<{
  vertices: number[][];
  faces?: number[][];
  cells?: number[][];
  wireframe: boolean;
}> = ({ vertices, faces, cells, wireframe }) => {
  const meshRef = useRef<Mesh>(null!);

  // Convert vertices and faces to Three.js geometry
  const positions = new Float32Array(vertices.flat());
  
  let indices: number[] = [];
  if (faces && faces.length > 0) {
    // Use faces for surface mesh
    indices = faces.flat();
  } else if (cells && cells.length > 0) {
    // Use cells (take first 3 vertices of each cell as triangle)
    cells.forEach((cell) => {
      if (cell.length >= 3) {
        indices.push(cell[0], cell[1], cell[2]);
      }
    });
  }

  const indicesArray = new Uint32Array(indices);

  return (
    <mesh ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={positions.length / 3}
          array={positions}
          itemSize={3}
        />
        {indicesArray.length > 0 && (
          <bufferAttribute
            attach="index"
            args={[indicesArray, 1]}
            count={indicesArray.length}
            array={indicesArray}
            itemSize={1}
          />
        )}
      </bufferGeometry>
      <meshStandardMaterial
        color="#2196f3"
        wireframe={wireframe}
        metalness={0.3}
        roughness={0.4}
      />
    </mesh>
  );
};

/**
 * Placeholder mesh (cube) when no data available
 */
const PlaceholderMesh: React.FC = () => {
  const meshRef = useRef<Mesh>(null!);

  useFrame((_, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.2;
      meshRef.current.rotation.y += delta * 0.3;
    }
  });

  return (
    <mesh ref={meshRef}>
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial color="#90caf9" wireframe />
    </mesh>
  );
};

/**
 * Main 3D Viewer Component
 */
export const MeshViewer3D: React.FC<MeshViewer3DProps> = ({
  vertices,
  faces,
  cells,
  wireframe = true,
}) => {
  const [showWireframe] = useState(wireframe);
  const controlsRef = useRef<any>(null);

  const handleResetView = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
  };

  const hasData = vertices && vertices.length > 0;

  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Controls */}
      <Stack
        direction="row"
        spacing={1}
        sx={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 1,
          bgcolor: 'background.paper',
          borderRadius: 1,
          p: 0.5,
        }}
      >
        <IconButton size="small" onClick={handleResetView} title="Reset View">
          <CenterFocusStrongIcon />
        </IconButton>
      </Stack>

      {/* Info overlay */}
      {!hasData && (
        <Box
          sx={{
            position: 'absolute',
            top: 16,
            left: 16,
            zIndex: 1,
            bgcolor: 'rgba(0, 0, 0, 0.6)',
            color: 'white',
            p: 2,
            borderRadius: 1,
          }}
        >
          <Typography variant="body2">
            3D visualization placeholder
          </Typography>
          <Typography variant="caption">
            Mesh data will be rendered here
          </Typography>
        </Box>
      )}

      {/* 3D Canvas */}
      <Canvas
        camera={{ position: [5, 5, 5], fov: 50 }}
        style={{ width: '100%', height: '100%' }}
      >
        <ambientLight intensity={0.5} />
        <directionalLight position={[10, 10, 5]} intensity={1} />
        <directionalLight position={[-10, -10, -5]} intensity={0.3} />

        {hasData ? (
          <MeshGeometry
            vertices={vertices}
            faces={faces}
            cells={cells}
            wireframe={showWireframe}
          />
        ) : (
          <PlaceholderMesh />
        )}

        <Grid
          args={[10, 10]}
          cellSize={0.5}
          cellThickness={0.5}
          cellColor="#6e6e6e"
          sectionSize={2}
          sectionThickness={1}
          sectionColor="#9d9d9d"
          fadeDistance={25}
          fadeStrength={1}
          followCamera={false}
        />

        <OrbitControls
          ref={controlsRef}
          enableDamping
          dampingFactor={0.05}
          minDistance={2}
          maxDistance={50}
        />
      </Canvas>
    </Box>
  );
};

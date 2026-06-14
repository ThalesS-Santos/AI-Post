"use client";

import { useMemo, useEffect } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";

const PARTICLE_COUNT   = 90;
const CONNECTION_DIST  = 1.8;
const MAX_CONNECTIONS  = 400;
const REPULSION_RADIUS = 1.4;
const REPULSION_FORCE  = 0.06;
const SPRING_FORCE     = 0.04;

function ParticleField() {
  const { mouse } = useThree();

  const { pointsGeo, linesGeo, original } = useMemo(() => {
    const original = new Float32Array(PARTICLE_COUNT * 3);
    const current  = new Float32Array(PARTICLE_COUNT * 3);

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const x = (Math.random() - 0.5) * 12;
      const y = (Math.random() - 0.5) * 8;
      const z = (Math.random() - 0.5) * 4;
      original[i * 3]     = current[i * 3]     = x;
      original[i * 3 + 1] = current[i * 3 + 1] = y;
      original[i * 3 + 2] = current[i * 3 + 2] = z;
    }

    const pg = new THREE.BufferGeometry();
    pg.setAttribute("position", new THREE.BufferAttribute(current, 3));

    const lineArr = new Float32Array(MAX_CONNECTIONS * 6);
    const lg = new THREE.BufferGeometry();
    lg.setAttribute("position", new THREE.BufferAttribute(lineArr, 3));
    lg.setDrawRange(0, 0);

    return { pointsGeo: pg, linesGeo: lg, original };
  }, []);

  useEffect(() => {
    return () => {
      pointsGeo.dispose();
      linesGeo.dispose();
    };
  }, [pointsGeo, linesGeo]);

  useFrame(() => {
    const mouseX = mouse.x * 6;
    const mouseY = mouse.y * 4;

    const pos     = pointsGeo.attributes.position.array as Float32Array;
    const linePos = linesGeo.attributes.position.array as Float32Array;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const ix = i * 3;
      const dx = pos[ix] - mouseX;
      const dy = pos[ix + 1] - mouseY;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < REPULSION_RADIUS && dist > 0.001) {
        const force = ((REPULSION_RADIUS - dist) / REPULSION_RADIUS) * REPULSION_FORCE;
        pos[ix]     += (dx / dist) * force;
        pos[ix + 1] += (dy / dist) * force;
      }

      pos[ix]     += (original[ix]     - pos[ix])     * SPRING_FORCE;
      pos[ix + 1] += (original[ix + 1] - pos[ix + 1]) * SPRING_FORCE;
      pos[ix + 2] += (original[ix + 2] - pos[ix + 2]) * SPRING_FORCE;
    }

    let lineCount = 0;

    for (let i = 0; i < PARTICLE_COUNT && lineCount < MAX_CONNECTIONS; i++) {
      for (let j = i + 1; j < PARTICLE_COUNT && lineCount < MAX_CONNECTIONS; j++) {
        const dx = pos[i * 3] - pos[j * 3];
        const dy = pos[i * 3 + 1] - pos[j * 3 + 1];
        const dz = pos[i * 3 + 2] - pos[j * 3 + 2];
        const dist = Math.sqrt(dx * dx + dy * dy + dz * dz);

        if (dist < CONNECTION_DIST) {
          const li = lineCount * 6;
          linePos[li]     = pos[i * 3];
          linePos[li + 1] = pos[i * 3 + 1];
          linePos[li + 2] = pos[i * 3 + 2];
          linePos[li + 3] = pos[j * 3];
          linePos[li + 4] = pos[j * 3 + 1];
          linePos[li + 5] = pos[j * 3 + 2];
          lineCount++;
        }
      }
    }

    pointsGeo.attributes.position.needsUpdate = true;
    linesGeo.attributes.position.needsUpdate  = true;
    linesGeo.setDrawRange(0, lineCount * 2);
  });

  return (
    <>
      <points geometry={pointsGeo}>
        <pointsMaterial
          size={0.07}
          color="#8b5cf6"
          transparent
          opacity={0.85}
          sizeAttenuation
        />
      </points>
      <lineSegments geometry={linesGeo}>
        <lineBasicMaterial color="#7c3aed" transparent opacity={0.18} />
      </lineSegments>
    </>
  );
}

export function ParticleMesh() {
  return (
    <Canvas
      camera={{ position: [0, 0, 9], fov: 60 }}
      style={{ position: "absolute", inset: 0, pointerEvents: "none" }}
      dpr={[1, 1.5]}
      gl={{ antialias: false, alpha: true }}
    >
      <ParticleField />
    </Canvas>
  );
}

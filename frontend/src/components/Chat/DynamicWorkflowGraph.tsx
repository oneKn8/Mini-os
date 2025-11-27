import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export interface WorkflowNode {
  id: string;
  label: string;
  type: 'agent' | 'tool' | 'decision' | 'action' | 'handoff' | 'parallel';
  status: 'pending' | 'active' | 'completed' | 'error';
  x?: number;
  y?: number;
  duration_ms?: number;
  agentId?: string; // For identifying agent owners
  capabilities?: string[]; // Agent capabilities
  toolsUsed?: number; // Count of tools used
}

export interface WorkflowEdge {
  from: string;
  to: string;
  label?: string;
  active?: boolean;
  type?: 'flow' | 'handoff' | 'data' | 'parallel'; // Edge type for styling
  dataType?: string; // Type of data being transferred
}

interface DynamicWorkflowGraphProps {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  width?: number;
  height?: number;
}

interface ParticleProps {
  edge: WorkflowEdge;
  nodes: Map<string, WorkflowNode>;
  delay: number;
}

const Particle: React.FC<ParticleProps> = ({ edge, nodes, delay }) => {
  const fromNode = nodes.get(edge.from);
  const toNode = nodes.get(edge.to);

  if (!fromNode || !toNode) return null;

  const fromX = fromNode.x || 0;
  const fromY = fromNode.y || 0;
  const toX = toNode.x || 0;
  const toY = toNode.y || 0;

  return (
    <motion.circle
      r="3"
      fill="#60a5fa"
      initial={{ cx: fromX, cy: fromY, opacity: 0 }}
      animate={{
        cx: toX,
        cy: toY,
        opacity: [0, 1, 1, 0],
      }}
      transition={{
        duration: 2,
        delay,
        ease: 'easeInOut',
        repeat: Infinity,
        repeatDelay: 1,
      }}
    />
  );
};

export const DynamicWorkflowGraph: React.FC<DynamicWorkflowGraphProps> = ({
  nodes,
  edges,
  width = 800,
  height = 600,
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [positionedNodes, setPositionedNodes] = useState<WorkflowNode[]>([]);
  const [viewBox, setViewBox] = useState({ x: 0, y: 0, width, height });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (nodes.length === 0) return;

    const positioned = layoutNodes(nodes, edges, width, height);
    setPositionedNodes(positioned);
  }, [nodes, edges, width, height]);

  const layoutNodes = (
    nodes: WorkflowNode[],
    edges: WorkflowEdge[],
    width: number,
    height: number
  ): WorkflowNode[] => {
    const nodeMap = new Map<string, WorkflowNode>();
    const levels = new Map<string, number>();
    const childrenMap = new Map<string, Set<string>>();

    nodes.forEach((node) => {
      nodeMap.set(node.id, { ...node });
      levels.set(node.id, 0);
      childrenMap.set(node.id, new Set());
    });

    edges.forEach((edge) => {
      const children = childrenMap.get(edge.from);
      if (children) children.add(edge.to);
    });

    const assignLevels = (nodeId: string, level: number) => {
      const currentLevel = levels.get(nodeId) || 0;
      if (level > currentLevel) {
        levels.set(nodeId, level);
      }
      const children = childrenMap.get(nodeId);
      if (children) {
        children.forEach((childId) => assignLevels(childId, level + 1));
      }
    };

    const rootNodes = nodes.filter(
      (node) => !edges.some((edge) => edge.to === node.id)
    );

    rootNodes.forEach((node) => assignLevels(node.id, 0));

    const maxLevel = Math.max(...Array.from(levels.values()));
    const levelGroups = new Map<number, WorkflowNode[]>();

    for (let i = 0; i <= maxLevel; i++) {
      levelGroups.set(i, []);
    }

    nodes.forEach((node) => {
      const level = levels.get(node.id) || 0;
      const group = levelGroups.get(level);
      if (group) group.push(node);
    });

    const positioned: WorkflowNode[] = [];
    const horizontalSpacing = width / (maxLevel + 2);
    const padding = 50;

    levelGroups.forEach((levelNodes, level) => {
      const verticalSpacing = (height - 2 * padding) / (levelNodes.length + 1);

      levelNodes.forEach((node, index) => {
        positioned.push({
          ...node,
          x: padding + horizontalSpacing * (level + 1),
          y: padding + verticalSpacing * (index + 1),
        });
      });
    });

    return positioned;
  };

  const getNodeColor = (status: string) => {
    switch (status) {
      case 'active':
        return '#3b82f6';
      case 'completed':
        return '#10b981';
      case 'error':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getNodeIcon = (type: string) => {
    switch (type) {
      case 'agent':
        return 'AG';
      case 'tool':
        return 'TL';
      case 'decision':
        return 'SW';
      case 'action':
        return 'FX';
      case 'handoff':
        return 'LP';
      case 'parallel':
        return '||';
      default:
        return '*';
    }
  };

  const getEdgeColor = (edge: WorkflowEdge) => {
    if (edge.type === 'handoff') return '#f59e0b'; // Amber for handoffs
    if (edge.type === 'data') return '#8b5cf6'; // Purple for data
    if (edge.type === 'parallel') return '#06b6d4'; // Cyan for parallel
    return edge.active ? '#60a5fa' : '#4b5563';
  };

  const getEdgeStrokeDasharray = (edge: WorkflowEdge) => {
    if (edge.type === 'handoff') return '8,4';
    if (edge.type === 'data') return '4,2';
    if (edge.type === 'parallel') return '2,2';
    return 'none';
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;

    const dx = (e.clientX - dragStart.x) * 2;
    const dy = (e.clientY - dragStart.y) * 2;

    setViewBox((prev) => ({
      ...prev,
      x: prev.x - dx,
      y: prev.y - dy,
    }));

    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const scale = e.deltaY > 0 ? 1.1 : 0.9;

    setViewBox((prev) => ({
      x: prev.x,
      y: prev.y,
      width: prev.width * scale,
      height: prev.height * scale,
    }));
  };

  const nodesMap = new Map(positionedNodes.map((node) => [node.id, node]));

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        No workflow data available
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-slate-900 rounded-lg overflow-hidden">
      <svg
        ref={svgRef}
        viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>

          <marker
            id="arrowhead"
            markerWidth="10"
            markerHeight="10"
            refX="9"
            refY="3"
            orient="auto"
          >
            <polygon points="0 0, 10 3, 0 6" fill="#60a5fa" />
          </marker>
        </defs>

        <AnimatePresence>
          {edges.map((edge, idx) => {
            const fromNode = nodesMap.get(edge.from);
            const toNode = nodesMap.get(edge.to);

            if (!fromNode || !toNode) return null;

            const isActive =
              edge.active ||
              fromNode.status === 'active' ||
              toNode.status === 'active';

            const edgeColor = getEdgeColor(edge);
            const strokeDash = getEdgeStrokeDasharray(edge);

            return (
              <g key={`${edge.from}-${edge.to}`}>
                <motion.line
                  x1={fromNode.x}
                  y1={fromNode.y}
                  x2={toNode.x}
                  y2={toNode.y}
                  stroke={isActive ? edgeColor : '#4b5563'}
                  strokeWidth={isActive ? 2 : 1.5}
                  strokeDasharray={strokeDash}
                  markerEnd="url(#arrowhead)"
                  initial={{ pathLength: 0, opacity: 0 }}
                  animate={{ pathLength: 1, opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.5, delay: idx * 0.1 }}
                />
                
                {/* Data transfer label */}
                {edge.dataType && (
                  <motion.g
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: idx * 0.1 + 0.3 }}
                  >
                    <rect
                      x={(fromNode.x! + toNode.x!) / 2 - 30}
                      y={(fromNode.y! + toNode.y!) / 2 - 10}
                      width="60"
                      height="16"
                      rx="4"
                      fill="#1e293b"
                      stroke="#334155"
                    />
                    <text
                      x={(fromNode.x! + toNode.x!) / 2}
                      y={(fromNode.y! + toNode.y!) / 2 + 2}
                      fill="#94a3b8"
                      fontSize="9"
                      textAnchor="middle"
                    >
                      {edge.dataType}
                    </text>
                  </motion.g>
                )}

                {isActive && (
                  <>
                    <Particle edge={edge} nodes={nodesMap} delay={0} />
                    <Particle edge={edge} nodes={nodesMap} delay={0.5} />
                    <Particle edge={edge} nodes={nodesMap} delay={1} />
                  </>
                )}

                {edge.label && (
                  <text
                    x={(fromNode.x! + toNode.x!) / 2}
                    y={(fromNode.y! + toNode.y!) / 2 - 5}
                    fill="#9ca3af"
                    fontSize="10"
                    textAnchor="middle"
                  >
                    {edge.label}
                  </text>
                )}
              </g>
            );
          })}
        </AnimatePresence>

        <AnimatePresence>
          {positionedNodes.map((node, idx) => (
            <motion.g
              key={node.id}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              transition={{
                type: 'spring',
                stiffness: 300,
                delay: idx * 0.1,
              }}
            >
              <motion.circle
                cx={node.x}
                cy={node.y}
                r={node.status === 'active' ? 35 : 30}
                fill={getNodeColor(node.status)}
                filter={node.status === 'active' ? 'url(#glow)' : undefined}
                animate={
                  node.status === 'active'
                    ? {
                        r: [30, 35, 30],
                        opacity: [0.8, 1, 0.8],
                      }
                    : {}
                }
                transition={
                  node.status === 'active'
                    ? {
                        duration: 2,
                        repeat: Infinity,
                        ease: 'easeInOut',
                      }
                    : {}
                }
              />

              <text
                x={node.x}
                y={node.y}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="18"
                fill="white"
              >
                {getNodeIcon(node.type)}
              </text>

              <text
                x={node.x}
                y={node.y! + 50}
                textAnchor="middle"
                fill="white"
                fontSize="12"
                fontWeight="500"
              >
                {node.label}
              </text>

              {node.duration_ms && node.status === 'completed' && (
                <text
                  x={node.x}
                  y={node.y! + 65}
                  textAnchor="middle"
                  fill="#9ca3af"
                  fontSize="10"
                >
                  {(node.duration_ms / 1000).toFixed(2)}s
                </text>
              )}
            </motion.g>
          ))}
        </AnimatePresence>
      </svg>

      <div className="absolute top-4 right-4 bg-slate-800/90 rounded-lg p-3 text-xs text-gray-300 space-y-1">
        <div className="font-semibold mb-2">Controls</div>
        <div>Drag to pan</div>
        <div>Scroll to zoom</div>
      </div>

      <div className="absolute bottom-4 left-4 bg-slate-800/90 rounded-lg p-3 text-xs text-gray-300 space-y-2">
        <div className="font-semibold mb-2">Node Status</div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-blue-500"></div>
          <span>Active</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-green-500"></div>
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span>Error</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gray-500"></div>
          <span>Pending</span>
        </div>
        
        <div className="font-semibold mt-3 mb-2">Edge Types</div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-blue-400"></div>
          <span>Flow</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-amber-500" style={{ backgroundImage: 'repeating-linear-gradient(90deg, transparent, transparent 4px, currentColor 4px, currentColor 8px)' }}></div>
          <span>Handoff</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-purple-500"></div>
          <span>Data</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-0.5 bg-cyan-500"></div>
          <span>Parallel</span>
        </div>
      </div>
    </div>
  );
};

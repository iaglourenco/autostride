import { useCallback, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";

const nodeColors = {
  boundary: "#ef4444",
  cache: "#f59e0b",
  database: "#3b82f6",
  external_service: "#8b5cf6",
  load_balancer: "#10b981",
  monitoring: "#06b6d4",
  security: "#f97316",
  service: "#6366f1",
  user: "#ec4899",
};

const GraphVisualization = ({ graphData }) => {
  // Convert API graph data to React Flow format
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!graphData) return { nodes: [], edges: [] };

    const padding = 200;
    const nodes = graphData.nodes.map((node) => ({
      id: node.id,
      type: "default",
      position: {
        x: node.position.x - padding / 2,
        y: node.position.y - padding / 2,
      },
      data: {
        label: (
          <div className="text-center">
            <div className="font-bold text-sm">
              {node.type.replace("_", " ")}
            </div>
            <div className="text-xs text-gray-500">{node.id}</div>
            <div className="text-xs text-gray-400">
              {(node.confidence * 100).toFixed(1)}%
            </div>
          </div>
        ),
      },
      style: {
        background: nodeColors[node.type] || "#gray",
        color: "white",
        border: "2px solid #fff",
        borderRadius: "8px",
        padding: "10px",
        fontSize: "12px",
        minWidth: "120px",
      },
    }));

    const edges = graphData.edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: "smoothstep",
      animated: true,
      style: {
        stroke: "#64748b",
        strokeWidth: 2,
      },
      markerEnd: {
        type: "arrowclosed",
        color: "#64748b",
      },
    }));

    return { nodes, edges };
  }, [graphData]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-500">Nenhum grafo para exibir</p>
      </div>
    );
  }

  return (
    <div className="h-[600px] bg-gray-50 rounded-lg border border-gray-300">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-left"
      >
        <Background color="#aaa" gap={16} />
        <Controls />
        <MiniMap
          nodeColor={(node) => {
            const type = graphData.nodes.find((n) => n.id === node.id)?.type;
            return nodeColors[type] || "#gray";
          }}
          maskColor="rgba(0, 0, 0, 0.1)"
        />
      </ReactFlow>
    </div>
  );
};

export default GraphVisualization;

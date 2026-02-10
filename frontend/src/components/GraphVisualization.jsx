import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Position,
  Handle,
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

// Custom node with handles on all sides
const CustomNode = ({ data }) => {
  return (
    <div
      style={{
        background: data.background,
        color: data.color,
        border: data.border,
        borderRadius: data.borderRadius,
        padding: data.padding,
        fontSize: data.fontSize,
        minWidth: data.minWidth,
      }}
    >
      <Handle type="target" position={Position.Top} id="top" />
      <Handle type="target" position={Position.Left} id="left" />
      <Handle type="source" position={Position.Right} id="right" />
      <Handle type="source" position={Position.Bottom} id="bottom" />
      {data.label}
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

const GraphVisualization = ({ graphData }) => {
  // Convert API graph data to React Flow format
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    if (!graphData) return { nodes: [], edges: [] };

    const padding = 200;
    const nodes = graphData.nodes.map((node) => ({
      id: node.id,
      type: "custom",
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
        background: nodeColors[node.type] || "#gray",
        color: "white",
        border: "2px solid #fff",
        borderRadius: "8px",
        padding: "10px",
        fontSize: "12px",
        minWidth: "120px",
      },
    }));

    // Prevent node overlapping
    const minDistance = 150; // Minimum distance between nodes
    const adjustedNodes = nodes.map((node, i) => {
      let newX = node.position.x;
      let newY = node.position.y;

      // Check collision with all other nodes
      for (let j = 0; j < nodes.length; j++) {
        if (i === j) continue;

        const other = nodes[j];
        const dx = node.position.x - other.position.x;
        const dy = node.position.y - other.position.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        // If nodes are too close, push them apart
        if (distance < minDistance && distance > 0) {
          const angle = Math.atan2(dy, dx);
          const pushDistance = (minDistance - distance) / 2;
          newX += Math.cos(angle) * pushDistance;
          newY += Math.sin(angle) * pushDistance;
        }
      }

      return {
        ...node,
        position: { x: newX, y: newY }
      };
    });

    // Create a map for quick node lookup
    const nodeMap = new Map(adjustedNodes.map(node => [node.id, node]));

    // Helper function to determine handle IDs based on node positions
    const getHandleIds = (sourceId, targetId) => {
      const sourceNode = nodeMap.get(sourceId);
      const targetNode = nodeMap.get(targetId);

      if (!sourceNode || !targetNode) {
        return { sourceHandle: "right", targetHandle: "left" };
      }

      const dx = targetNode.position.x - sourceNode.position.x;
      const dy = targetNode.position.y - sourceNode.position.y;
      const absDx = Math.abs(dx);
      const absDy = Math.abs(dy);

      // Determine handle IDs based on relative positions
      let sourceHandle = "right";
      let targetHandle = "left";

      if (absDx > absDy) {
        // Horizontal alignment is more significant
        if (dx > 0) {
          sourceHandle = "right";
          targetHandle = "left";
        } else {
          sourceHandle = "left";
          targetHandle = "right";
        }
      } else {
        // Vertical alignment is more significant
        if (dy > 0) {
          sourceHandle = "bottom";
          targetHandle = "top";
        } else {
          sourceHandle = "top";
          targetHandle = "bottom";
        }
      }

      return { sourceHandle, targetHandle };
    };

    const edges = graphData.edges.map((edge) => {
      const { sourceHandle, targetHandle } = getHandleIds(edge.source, edge.target);

      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle,
        targetHandle,
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
      };
    });

    return { nodes: adjustedNodes, edges };
  }, [graphData]);

  // eslint-disable-next-line no-unused-vars
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  // eslint-disable-next-line no-unused-vars
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
        <p className="text-gray-500">Nenhum grafo para exibir</p>
      </div>
    );
  }

  return (
    <div className="h-150 bg-gray-50 rounded-lg border border-gray-300">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
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

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

// Custom node with dynamic handles - only creates handles that have connections
const CustomNode = ({ data }) => {
  const { handles = {}, isBoundary = false } = data;

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
        minHeight: isBoundary ? data.minHeight : 'auto',
        width: isBoundary ? data.width : 'auto',
        height: isBoundary ? data.height : 'auto',
      }}
    >
      {/* Top handles - only render if used */}
      {handles.top && (
        <Handle
          type={handles.top.isSource && handles.top.isTarget ? "source" : handles.top.isSource ? "source" : "target"}
          position={Position.Top}
          id="top"
          isConnectable={true}
        />
      )}

      {/* Right handles - only render if used */}
      {handles.right && (
        <Handle
          type={handles.right.isSource && handles.right.isTarget ? "source" : handles.right.isSource ? "source" : "target"}
          position={Position.Right}
          id="right"
          isConnectable={true}
        />
      )}

      {/* Bottom handles - only render if used */}
      {handles.bottom && (
        <Handle
          type={handles.bottom.isSource && handles.bottom.isTarget ? "source" : handles.bottom.isSource ? "source" : "target"}
          position={Position.Bottom}
          id="bottom"
          isConnectable={true}
        />
      )}

      {/* Left handles - only render if used */}
      {handles.left && (
        <Handle
          type={handles.left.isSource && handles.left.isTarget ? "source" : handles.left.isSource ? "source" : "target"}
          position={Position.Left}
          id="left"
          isConnectable={true}
        />
      )}

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

    // Create a map from API nodes for quick lookup
    const apiNodeMap = new Map(graphData.nodes.map(n => [n.id, n]));

    // First pass: create nodes with basic properties
    const nodes = graphData.nodes.map((node) => {
      const isBoundary = node.type === "boundary";

      return {
        id: node.id,
        type: "custom",
        // Position calculation: if has parent, use relative position
        position: node.parent_id
          ? {
              // Relative to parent's bbox
              x: node.bbox[0] - apiNodeMap.get(node.parent_id).bbox[0] + 10,
              y: node.bbox[1] - apiNodeMap.get(node.parent_id).bbox[1] + 30,
            }
          : {
              // Absolute position for root nodes
              x: node.position.x - padding / 2,
              y: node.position.y - padding / 2,
            },
        // Set parent relationship
        parentNode: node.parent_id || undefined,
        extent: node.parent_id ? "parent" : undefined,
        style: isBoundary
          ? {
              width: node.width || 300,
              height: node.height || 200,
              zIndex: -1, // Boundaries behind other nodes
            }
          : {},
        data: {
          label: (
            <div className="text-center">
              <div className="font-bold text-sm">
                {node.type.replace("_", " ")}
              </div>
              {!isBoundary && (
                <>
                  <div className="text-xs text-gray-500">{node.id}</div>
                  <div className="text-xs text-gray-400">
                    {(node.confidence * 100).toFixed(1)}%
                  </div>
                </>
              )}
            </div>
          ),
          background: isBoundary
            ? "rgba(239, 68, 68, 0.1)" // Transparent red for boundaries
            : nodeColors[node.type] || "#gray",
          color: isBoundary ? "#ef4444" : "white",
          border: isBoundary ? "2px dashed #ef4444" : "2px solid #fff",
          borderRadius: "8px",
          padding: isBoundary ? "20px" : "10px",
          fontSize: "12px",
          minWidth: isBoundary ? node.width : "120px",
          minHeight: isBoundary ? node.height : undefined,
          width: isBoundary ? node.width : undefined,
          height: isBoundary ? node.height : undefined,
          isBoundary,
          handles: {}, // Will be populated based on edges
        },
      };
    });

    // Skip overlap prevention for child nodes (they're positioned relative to parent)
    // Only adjust root-level nodes that might overlap
    const minDistance = 150;
    const adjustedNodes = nodes.map((node, i) => {
      // Skip adjustment for child nodes (relative positioning)
      if (node.parentNode) return node;

      let newX = node.position.x;
      let newY = node.position.y;

      // Check collision only with other root nodes
      for (let j = 0; j < nodes.length; j++) {
        if (i === j) continue;

        const other = nodes[j];
        // Skip if other is a child node
        if (other.parentNode) continue;

        const dx = node.position.x - other.position.x;
        const dy = node.position.y - other.position.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

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

    // Helper function to calculate absolute position of a node (considering parent hierarchy)
    const getAbsolutePosition = (nodeId) => {
      const node = nodeMap.get(nodeId);
      if (!node) return { x: 0, y: 0 };

      let absX = node.position.x;
      let absY = node.position.y;

      // If node has a parent, add parent's absolute position
      if (node.parentNode) {
        const parentPos = getAbsolutePosition(node.parentNode);
        absX += parentPos.x;
        absY += parentPos.y;
      }

      return { x: absX, y: absY };
    };

    // Helper function to determine handle positions based on absolute node positions
    const determineHandlePosition = (sourceId, targetId) => {
      const sourceNode = nodeMap.get(sourceId);
      const targetNode = nodeMap.get(targetId);

      if (!sourceNode || !targetNode) {
        return { sourceHandle: "right", targetHandle: "left" };
      }

      // Get absolute positions in the canvas
      const sourcePos = getAbsolutePosition(sourceId);
      const targetPos = getAbsolutePosition(targetId);

      const dx = targetPos.x - sourcePos.x;
      const dy = targetPos.y - sourcePos.y;
      const absDx = Math.abs(dx);
      const absDy = Math.abs(dy);

      let sourceHandle = "right";
      let targetHandle = "left";

      if (absDx > absDy) {
        // Horizontal alignment dominant
        if (dx > 0) {
          sourceHandle = "right";
          targetHandle = "left";
        } else {
          sourceHandle = "left";
          targetHandle = "right";
        }
      } else {
        // Vertical alignment dominant
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

    // Second pass: analyze edges to determine which handles each node needs
    const handleUsage = new Map();

    graphData.edges.forEach((edge) => {
      const { sourceHandle, targetHandle } = determineHandlePosition(edge.source, edge.target);

      // Track source node handle usage
      if (!handleUsage.has(edge.source)) {
        handleUsage.set(edge.source, {});
      }
      const sourceHandles = handleUsage.get(edge.source);
      if (!sourceHandles[sourceHandle]) {
        sourceHandles[sourceHandle] = { isSource: false, isTarget: false };
      }
      sourceHandles[sourceHandle].isSource = true;

      // Track target node handle usage
      if (!handleUsage.has(edge.target)) {
        handleUsage.set(edge.target, {});
      }
      const targetHandles = handleUsage.get(edge.target);
      if (!targetHandles[targetHandle]) {
        targetHandles[targetHandle] = { isSource: false, isTarget: false };
      }
      targetHandles[targetHandle].isTarget = true;
    });

    // Update nodes with handle information
    adjustedNodes.forEach(node => {
      const handles = handleUsage.get(node.id);
      if (handles) {
        node.data.handles = handles;
      }
    });

    // Create edges with determined handle positions
    const edges = graphData.edges.map((edge) => {
      const { sourceHandle, targetHandle } = determineHandlePosition(edge.source, edge.target);

      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceHandle,
        targetHandle,
        type: "default",
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

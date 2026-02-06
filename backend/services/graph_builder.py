import numpy as np
from typing import List, Dict, Tuple
from schemas.api_models import Graph, Node, Edge, Position


# Mapping of class indices to component names
CLASS_NAMES = {
    0: "boundary",
    1: "cache",
    2: "database",
    3: "external_service",
    4: "load_balancer",
    5: "monitoring",
    6: "security",
    7: "service",
    8: "user",
    9: "fluxo_seta",  # Arrow flow
}


class GraphBuilder:
    """Builds a graph from YOLO detection results."""

    def __init__(self):
        self.component_classes = list(range(9))  # Classes 0-8 are components
        self.arrow_class = 9  # Class 9 is arrow flow

    def build_graph(self, yolo_results) -> Graph:
        """
        Build a graph from YOLO results.

        Args:
            yolo_results: YOLO prediction results

        Returns:
            Graph object with nodes and edges
        """
        nodes = self._extract_nodes(yolo_results)
        edges = self._extract_edges(yolo_results, nodes)

        return Graph(nodes=nodes, edges=edges)

    def _extract_nodes(self, yolo_results) -> List[Node]:
        """Extract component nodes from detections."""
        nodes = []

        if not hasattr(yolo_results, "boxes") or yolo_results.boxes is None:
            return nodes

        boxes = yolo_results.boxes

        for idx, box in enumerate(boxes):
            cls_id = int(box.cls[0])

            # Only process component classes (0-8), not arrows (9)
            if cls_id not in self.component_classes:
                continue

            # Get bounding box coordinates
            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = xyxy

            # Calculate center position
            center_x = (x1 + x2) / 2
            center_y = (y1 + y2) / 2

            # Get confidence
            confidence = float(box.conf[0])

            # Create node
            node = Node(
                id=f"node_{idx}",
                type=CLASS_NAMES[cls_id],
                position=Position(x=float(center_x), y=float(center_y)),
                confidence=confidence,
                bbox=[float(x1), float(y1), float(x2), float(y2)],
            )

            nodes.append(node)

        return nodes

    def _extract_edges(self, yolo_results, nodes: List[Node]) -> List[Edge]:
        """Extract edges from arrow detections and connect to nearest nodes."""
        edges = []

        if not hasattr(yolo_results, "boxes") or yolo_results.boxes is None:
            return edges

        if not hasattr(yolo_results, "keypoints") or yolo_results.keypoints is None:
            return edges

        boxes = yolo_results.boxes
        keypoints_data = yolo_results.keypoints

        edge_idx = 0

        for box_idx, box in enumerate(boxes):
            cls_id = int(box.cls[0])

            # Only process arrow class (9)
            if cls_id != self.arrow_class:
                continue

            # Get keypoints for this arrow
            # keypoints shape: (num_keypoints, 3) where 3 = (x, y, visibility)
            kpts = keypoints_data.data[box_idx].cpu().numpy()

            if len(kpts) < 2:
                continue

            # Get start and end points of the arrow
            start_point = kpts[0][:2]  # (x, y) of first keypoint
            end_point = kpts[1][:2]  # (x, y) of second keypoint

            # Find nearest nodes to start and end points
            source_node = self._find_nearest_node(start_point, nodes)
            target_node = self._find_nearest_node(end_point, nodes)

            # Create edge if both nodes are found and they are different
            if source_node and target_node and source_node.id != target_node.id:
                edge = Edge(
                    id=f"edge_{edge_idx}",
                    source=source_node.id,
                    target=target_node.id,
                    keypoints=[
                        [float(start_point[0]), float(start_point[1])],
                        [float(end_point[0]), float(end_point[1])],
                    ],
                )
                edges.append(edge)
                edge_idx += 1

        return edges

    def _find_nearest_node(self, point: np.ndarray, nodes: List[Node]) -> Node | None:
        """
        Find the nearest node to a given point.

        Args:
            point: (x, y) coordinates
            nodes: List of nodes

        Returns:
            Nearest node or None
        """
        if not nodes:
            return None

        min_distance = float("inf")
        nearest_node = None

        for node in nodes:
            # Calculate distance from point to node center
            distance = np.sqrt(
                (node.position.x - point[0]) ** 2 + (node.position.y - point[1]) ** 2
            )

            if distance < min_distance:
                min_distance = distance
                nearest_node = node

        return nearest_node

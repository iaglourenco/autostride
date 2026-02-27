import numpy as np
from typing import List, Optional
from schemas.api_models import Graph, Node, Edge, Position

# Mantemos o mapeamento, mas vamos usar para identificar quem pode ser pai
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
    9: "fluxo_seta",
}

# Classes que funcionam como containers (Boundaries, Subnets, Groups)
CONTAINER_CLASSES = [0]


class GraphBuilder:
    """
    Constrói um grafo hierárquico onde nós podem conter outros nós.
    Essencial para reconstrução visual e análise de segurança (STRIDE).
    """

    def __init__(self, min_confidence: float = 0.5):
        self.component_classes = list(range(9))
        self.arrow_class = 9
        self.min_confidence = min_confidence

    def build_graph(self, yolo_results) -> Graph:
        # 1. Extração bruta dos nós
        nodes = self._extract_nodes(yolo_results)

        # 2. Construção da Hierarquia (Quem está dentro de quem?)
        # Isso modifica os objetos 'nodes' adicionando parent_id
        nodes = self._build_hierarchy(nodes)

        # 3. Extração de Arestas com lógica de profundidade (Z-index)
        edges = self._extract_edges(yolo_results, nodes)

        return Graph(nodes=nodes, edges=edges)

    def _extract_nodes(self, yolo_results) -> List[Node]:
        nodes = []
        if not hasattr(yolo_results, "boxes") or yolo_results.boxes is None:
            return nodes

        for idx, box in enumerate(yolo_results.boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            if conf < self.min_confidence or cls_id not in self.component_classes:
                continue

            xyxy = box.xyxy[0].cpu().numpy()
            x1, y1, x2, y2 = xyxy

            # Calculamos área para saber quem é "menor" (o mais interno)
            area = (x2 - x1) * (y2 - y1)

            node = Node(
                id=f"node_{idx}",
                type=CLASS_NAMES[cls_id],
                position=Position(x=float((x1 + x2) / 2), y=float((y1 + y2) / 2)),
                confidence=conf,
                bbox=[float(x1), float(y1), float(x2), float(y2)],
                # Campos novos sugeridos para reconstrução:
                width=float(x2 - x1),
                height=float(y2 - y1),
                area=float(area),
                parent_id=None,  # Será preenchido depois
                children=[],  # Será preenchido depois
            )
            nodes.append(node)

        return nodes

    def _build_hierarchy(self, nodes: List[Node]) -> List[Node]:
        """
        Detecta quais nós estão dentro de boundaries.
        Lógica: Um nó é filho da MENOR boundary que o contém totalmente.
        """
        # Separar containers (boundaries) de itens normais
        containers = [n for n in nodes if n.type == "boundary"]

        # Ordenar containers por área (do menor para o maior)
        # Isso garante que se A está dentro de Subnet, e Subnet está dentro de VPC,
        # A detecte Subnet primeiro.
        containers.sort(key=lambda x: x.area)

        for node in nodes:
            # Um container não pode ser pai dele mesmo, mas pode ser pai de outro container
            # (ex: VPC contém Subnet)

            # Procurar o primeiro container (o menor possível) que contém este nó
            parent = None
            for container in containers:
                if node.id == container.id:
                    continue

                if self._is_contained(node.bbox, container.bbox):
                    parent = container
                    break  # Encontrei o menor pai possível, paro aqui.

            if parent:
                node.parent_id = parent.id
                parent.children.append(node.id)

        return nodes

    def _extract_edges(self, yolo_results, nodes: List[Node]) -> List[Edge]:
        edges = []
        if not hasattr(yolo_results, "keypoints") or yolo_results.keypoints is None:
            return edges

        boxes = yolo_results.boxes
        kpts_data = yolo_results.keypoints

        edge_idx = 0
        for i, box in enumerate(boxes):
            if int(box.cls[0]) != self.arrow_class:
                continue

            kpts = kpts_data.data[i].cpu().numpy()
            if len(kpts) < 2:
                continue

            # Ponto 1 (Origem) e Ponto 2 (Destino)
            p1, p2 = kpts[0], kpts[1]

            # Se a visibilidade for muito baixa, ignora
            if p1[2] < 0.3 or p2[2] < 0.3:
                continue

            start_xy = p1[:2]
            end_xy = p2[:2]

            # Usamos uma busca que prioriza o nó mais "profundo" na hierarquia
            source = self._find_best_node_at_location(start_xy, nodes)
            target = self._find_best_node_at_location(end_xy, nodes)

            if source and target and source.id != target.id:
                edge = Edge(
                    id=f"edge_{edge_idx}",
                    source=source.id,
                    target=target.id,
                    # Adicionamos metadados de boundary crossing para o STRIDE
                    cross_boundary=(source.parent_id != target.parent_id),
                    keypoints=[start_xy.tolist(), end_xy.tolist()],
                )
                edges.append(edge)
                edge_idx += 1

        return edges

    def _find_best_node_at_location(
        self, point: np.ndarray, nodes: List[Node]
    ) -> Optional[Node]:
        """
        Encontra o nó mais específico (menor área) que contém o ponto.
        Se o ponto estiver dentro de um Service e de uma Boundary, retorna o Service.
        Prioriza nós não-container para conexões.
        """
        candidates = []

        px, py = point

        for node in nodes:
            x1, y1, x2, y2 = node.bbox
            # Tolerância aumentada para capturar melhor as conexões nas bordas
            padding = 15.0
            if (x1 - padding) <= px <= (x2 + padding) and (y1 - padding) <= py <= (
                y2 + padding
            ):
                candidates.append(node)

        if not candidates:
            # Fallback: Se não caiu dentro de ninguém, busca o mais próximo por distância
            # Threshold aumentado para maior tolerância
            return self._find_nearest_by_distance(point, nodes, threshold=100.0)

        # Se o ponto está dentro de vários (ex: Boundary e Service),
        # PRIORIZA nós não-container (services, databases, etc)
        non_containers = [n for n in candidates if n.type not in ["boundary"]]

        if non_containers:
            # Ordena por área, pega o menor (mais específico)
            non_containers.sort(key=lambda n: n.area)
            return non_containers[0]

        # Se só tem containers, pega o menor
        candidates.sort(key=lambda n: n.area)
        return candidates[0]

    def _find_nearest_by_distance(self, point, nodes, threshold):
        """Busca o nó mais próximo ao ponto, priorizando nós não-container."""
        best_node = None
        min_dist = float("inf")

        # Primeiro tenta encontrar entre nós não-container
        non_containers = [n for n in nodes if n.type not in ["boundary"]]
        candidates = non_containers if non_containers else nodes

        for node in candidates:
            dist = np.sqrt(
                (node.position.x - point[0]) ** 2 + (node.position.y - point[1]) ** 2
            )
            if dist < min_dist and dist < threshold:
                min_dist = dist
                best_node = node

        return best_node

    def _is_contained(self, inner_bbox, outer_bbox, threshold: float = 0.8) -> bool:
        """
        Verifica se o nó 'inner' está substancialmente contido no 'outer'.
        Usa Interseção sobre Área (IoA) para tolerar imprecisões de detecção.
        """
        ix1, iy1, ix2, iy2 = inner_bbox
        ox1, oy1, ox2, oy2 = outer_bbox

        # 1. Calcular as coordenadas do retângulo de interseção
        x1_inter = max(ix1, ox1)
        y1_inter = max(iy1, oy1)
        x2_inter = min(ix2, ox2)
        y2_inter = min(iy2, oy2)

        # 2. Calcular largura e altura da interseção (garantindo que não sejam negativas)
        width_inter = max(0, x2_inter - x1_inter)
        height_inter = max(0, y2_inter - y1_inter)

        # 3. Calcular áreas
        area_inter = width_inter * height_inter
        area_inner = (ix2 - ix1) * (iy2 - iy1)

        if area_inner <= 0:
            return False

        # 4. Verificar se a porcentagem de sobreposição atinge o limite (ex: 80%)
        overlap_ratio = area_inter / area_inner
        return overlap_ratio >= threshold

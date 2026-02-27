# yolo_architecture_backend.py
from label_studio_ml.model import LabelStudioMLBase
from ultralytics.models import YOLO
import requests
from io import BytesIO
from PIL import Image
import os


class YOLOArchitectureBackend(LabelStudioMLBase):

    def __init__(self, **kwargs):
        super(YOLOArchitectureBackend, self).__init__(**kwargs)

        # Carregue seu modelo YOLOv11-pose customizado
        self.model = YOLO(r"model/model.pt")

        # Configure confiança mínima
        self.conf_threshold = 0.25
        self.keypoint_conf_threshold = 0.3

        # Mapeamento de classes de componentes (índice -> nome)
        # Ajuste conforme a ordem que você treinou o modelo
        self.component_names = [
            "boundary",
            "cache",
            "database",
            "external_service",
            "load_balancer",
            "monitoring",
            "security",
            "service",
            "user",
        ]

    def predict(self, tasks, **kwargs):
        """Faz predições para uma lista de tasks"""
        predictions = []

        for task in tasks:
            # Pega URL/caminho da imagem
            image_url = task["data"]["image"]

            # Baixa e processa imagem
            image = self._get_image(image_url)
            img_width, img_height = image.size

            # Roda YOLO pose
            results = self.model(image, conf=self.conf_threshold)

            # Converte para formato Label Studio
            prediction_result = self._convert_to_ls_format(
                results[0], img_width, img_height
            )

            predictions.append(
                {
                    "result": prediction_result,
                    "score": self._get_average_score(results[0]),
                    "model_version": "yolov11-architecture-v1",
                }
            )

        return predictions

    def _get_image(self, url):
        """Baixa imagem da URL ou carrega do caminho local"""
        if url.startswith("http"):
            response = requests.get(url)
            image = Image.open(BytesIO(response.content))
        else:
            import os

            # Remove prefixos do Label Studio
            clean_url = url.replace("/data/upload/", "").replace(
                "/data/local-files/?d=", ""
            )
            clean_url = clean_url.replace("\\", "/")  # Normaliza barras

            base_path = (
                r"C:\Users\Iago\AppData\Local\label-studio\label-studio\media\upload"
            )

            full_path = os.path.join(base_path, clean_url)

            # Debug: mostra o caminho que está tentando abrir
            print(f"Tentando abrir: {full_path}")

            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {full_path}")

            image = Image.open(full_path)

        return image

    def _convert_to_ls_format(self, result, img_width, img_height):
        """Converte resultados YOLO-pose para formato Label Studio"""
        predictions = []

        # Verifica se há detecções
        if result.boxes is None or len(result.boxes) == 0:
            return predictions

        boxes = result.boxes
        keypoints = result.keypoints if hasattr(result, "keypoints") else None

        for i in range(len(boxes)):
            # === BOUNDING BOX (Componentes) ===
            box = boxes.xyxy[i].cpu().numpy()
            conf = float(boxes.conf[i].cpu().numpy())
            cls = int(boxes.cls[i].cpu().numpy())

            # Pega nome da classe
            if cls < len(self.component_names):
                label = self.component_names[cls]
            else:
                label = self.model.names[cls]  # Fallback para nome do modelo

            if conf >= self.conf_threshold:
                # Coordenadas em pixels
                xmin, ymin, xmax, ymax = box

                # Converte para porcentagens (Label Studio usa 0-100)
                x = (xmin / img_width) * 100
                y = (ymin / img_height) * 100
                width = ((xmax - xmin) / img_width) * 100
                height = ((ymax - ymin) / img_height) * 100

                # Adiciona bounding box do componente
                predictions.append(
                    {
                        "from_name": "label",
                        "to_name": "image",
                        "type": "rectanglelabels",
                        "value": {
                            "x": float(x),
                            "y": float(y),
                            "width": float(width),
                            "height": float(height),
                            "rectanglelabels": [label],
                        },
                        "score": float(conf),
                    }
                )

                # === KEYPOINTS (Ponta e Cauda das setas de fluxo) ===
                if keypoints is not None and len(keypoints) > i:
                    kp_data = (
                        keypoints[i].xy.cpu().numpy()[0]
                    )  # shape: (num_keypoints, 2)
                    kp_conf = (
                        keypoints[i].conf.cpu().numpy()[0]
                        if hasattr(keypoints[i], "conf")
                        else None
                    )

                    # Para seu caso: cada componente pode ter keypoints representando
                    # pontos de conexão (ponta e cauda de setas)
                    # Assumindo que você treinou com pares de keypoints por conexão

                    for kp_idx, (kp_x, kp_y) in enumerate(kp_data):
                        # Verifica confiança do keypoint
                        if (
                            kp_conf is not None
                            and kp_conf[kp_idx] < self.keypoint_conf_threshold
                        ):
                            continue

                        # Ignora keypoints não detectados (0, 0)
                        if kp_x == 0 and kp_y == 0:
                            continue

                        # Converte para porcentagens
                        kp_x_pct = (kp_x / img_width) * 100
                        kp_y_pct = (kp_y / img_height) * 100

                        # Todos os keypoints são "fluxo_seta" conforme seu config
                        predictions.append(
                            {
                                "from_name": "kp-label",
                                "to_name": "image",
                                "type": "keypointlabels",
                                "value": {
                                    "x": float(kp_x_pct),
                                    "y": float(kp_y_pct),
                                    "width": 0.8,  # Tamanho visual do ponto
                                    "keypointlabels": ["fluxo_seta"],
                                },
                                "score": (
                                    float(kp_conf[kp_idx])
                                    if kp_conf is not None
                                    else float(conf)
                                ),
                            }
                        )

        return predictions

    def _get_average_score(self, result):
        """Calcula confiança média das predições"""
        if result.boxes is not None and len(result.boxes) > 0:
            return float(result.boxes.conf.mean().cpu().numpy())
        return 0.0

    def fit(self, tasks, workdir=None, **kwargs):
        """
        Método de treinamento desabilitado - apenas pre-labeling
        """
        print(f"Treinamento chamado com {len(tasks) if tasks else 0} anotações")
        print("⚠ Treinamento desabilitado - este backend é apenas para pre-labeling")

        return {}

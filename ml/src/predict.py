from ultralytics.models import YOLO
import cv2
import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk
from pathlib import Path


class ModelComparator:
    def __init__(self, root):
        self.root = root
        self.root.title("AutoStride - Comparador de Modelos")
        self.root.geometry("1400x900")

        # Paths
        self.base_path = Path(__file__).parent.parent
        self.runs_path = self.base_path / "runs" / "detect"

        # Variáveis
        self.models = {}
        self.current_image = None
        self.conf_threshold = 0.5
        self.photo_references = []  # Keep references to prevent garbage collection

        # Carregar modelos disponíveis
        self.load_models()

        # Criar interface
        self.create_widgets()

    def load_models(self):
        """Carrega todos os modelos disponíveis em runs/detect"""
        print("Carregando modelos...")
        for model_dir in self.runs_path.iterdir():
            if model_dir.is_dir():
                best_weight = model_dir / "weights" / "best.pt"
                if best_weight.exists():
                    try:
                        model = YOLO(str(best_weight))
                        self.models[model_dir.name] = {
                            "model": model,
                            "path": str(best_weight),
                        }
                        print(f"✓ Modelo carregado: {model_dir.name}")
                    except Exception as e:
                        print(f"✗ Erro ao carregar {model_dir.name}: {e}")

        if not self.models:
            print("⚠ Nenhum modelo encontrado!")
        else:
            print(f"\nTotal de modelos carregados: {len(self.models)}")

    def create_widgets(self):
        """Cria a interface gráfica"""
        # Frame superior - Controles
        control_frame = tk.Frame(self.root, bg="#2c3e50", padx=10, pady=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        # Botão para selecionar imagem
        self.btn_select = tk.Button(
            control_frame,
            text="📁 Selecionar Imagem",
            command=self.select_image,
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
        )
        self.btn_select.pack(side=tk.LEFT, padx=5)

        # Slider de confiança
        tk.Label(
            control_frame,
            text="Confiança:",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="white",
        ).pack(side=tk.LEFT, padx=(20, 5))

        self.conf_scale = tk.Scale(
            control_frame,
            from_=0.1,
            to=1.0,
            resolution=0.05,
            orient=tk.HORIZONTAL,
            length=200,
            command=self.update_confidence,
            bg="#34495e",
            fg="white",
            highlightthickness=0,
        )
        self.conf_scale.set(self.conf_threshold)
        self.conf_scale.pack(side=tk.LEFT, padx=5)

        self.conf_label = tk.Label(
            control_frame,
            text=f"{self.conf_threshold:.2f}",
            font=("Arial", 10, "bold"),
            bg="#2c3e50",
            fg="#2ecc71",
        )
        self.conf_label.pack(side=tk.LEFT, padx=5)

        # Botão para processar
        self.btn_process = tk.Button(
            control_frame,
            text="🚀 Processar Todos os Modelos",
            command=self.process_all_models,
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            padx=20,
            pady=10,
            cursor="hand2",
            state=tk.DISABLED,
        )
        self.btn_process.pack(side=tk.LEFT, padx=5)

        # Label de status
        self.status_label = tk.Label(
            control_frame,
            text="Aguardando imagem...",
            font=("Arial", 10),
            bg="#2c3e50",
            fg="#ecf0f1",
        )
        self.status_label.pack(side=tk.RIGHT, padx=10)

        # Frame para resultados (com scroll)
        canvas_frame = tk.Frame(self.root)
        canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas com scrollbar
        self.canvas = tk.Canvas(canvas_frame, bg="#ecf0f1")
        scrollbar_y = ttk.Scrollbar(
            canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview
        )
        scrollbar_x = ttk.Scrollbar(
            canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview
        )

        self.results_frame = tk.Frame(self.canvas, bg="#ecf0f1")

        self.canvas.create_window((0, 0), window=self.results_frame, anchor=tk.NW)
        self.canvas.configure(
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set
        )

        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.results_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

    def update_confidence(self, value):
        """Atualiza o valor de confiança"""
        self.conf_threshold = float(value)
        self.conf_label.config(text=f"{self.conf_threshold:.2f}")

    def select_image(self):
        """Seleciona uma imagem para processar"""
        file_path = filedialog.askopenfilename(
            title="Selecionar Imagem",
            filetypes=[
                ("Imagens", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("Todos os arquivos", "*.*"),
            ],
        )

        if file_path:
            self.current_image = file_path
            self.btn_process.config(state=tk.NORMAL)
            self.status_label.config(
                text=f"Imagem: {Path(file_path).name}", fg="#2ecc71"
            )

    def process_all_models(self):
        """Processa a imagem com todos os modelos"""
        if not self.current_image:
            return

        # Limpar resultados anteriores
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.photo_references.clear()  # Clear old photo references

        self.status_label.config(text="Processando...", fg="#f39c12")
        self.root.update()

        # Processar cada modelo
        results = {}
        for idx, (model_name, model_info) in enumerate(self.models.items()):
            try:
                print(f"Processando com {model_name}...")
                model = model_info["model"]
                result = model(self.current_image, conf=self.conf_threshold)[0]

                # Plotar resultado
                im_array = result.plot()
                im_array = cv2.cvtColor(im_array, cv2.COLOR_BGR2RGB)

                # Contar detecções
                n_detections = len(result.boxes) if hasattr(result, "boxes") else 0

                results[model_name] = {
                    "image": im_array,
                    "detections": n_detections,
                    "boxes": result.boxes if hasattr(result, "boxes") else None,
                }

            except Exception as e:
                print(f"Erro ao processar com {model_name}: {e}")
                results[model_name] = None

        # Mostrar resultados
        self.display_results(results)
        self.status_label.config(text="Processamento concluído!", fg="#2ecc71")

    def display_results(self, results):
        """Exibe os resultados lado a lado"""
        # Calcular quantas colunas (máximo 2)
        n_models = len([r for r in results.values() if r is not None])
        n_cols = min(2, n_models)

        row = 0
        col = 0

        for model_name, result in results.items():
            if result is None:
                continue

            # Frame para cada modelo
            model_frame = tk.Frame(
                self.results_frame, bg="white", relief=tk.RAISED, borderwidth=2
            )
            model_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # Título
            title_frame = tk.Frame(model_frame, bg="#34495e", pady=5)
            title_frame.pack(fill=tk.X)

            tk.Label(
                title_frame,
                text=model_name,
                font=("Arial", 12, "bold"),
                bg="#34495e",
                fg="white",
            ).pack()

            tk.Label(
                title_frame,
                text=f"Detecções: {result['detections']}",
                font=("Arial", 10),
                bg="#34495e",
                fg="#2ecc71",
            ).pack()

            # Imagem
            img = Image.fromarray(result["image"])
            img.thumbnail((600, 500), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)

            img_label = tk.Label(model_frame, image=photo, bg="white")
            self.photo_references.append(photo)  # Manter referência
            img_label.pack(padx=10, pady=10)

            # Atualizar grid
            col += 1
            if col >= n_cols:
                col = 0
                row += 1

        # Configurar grid weights
        for i in range(n_cols):
            self.results_frame.grid_columnconfigure(i, weight=1)


def main():
    root = tk.Tk()
    app = ModelComparator(root)
    root.mainloop()


if __name__ == "__main__":
    main()

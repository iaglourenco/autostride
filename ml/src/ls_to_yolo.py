import json
import os
import shutil
import random

# ==========================================
# 1. CONFIGURAÇÕES - AJUSTE SEUS CAMINHOS
# ==========================================
ROOT_DIR = r"C:\Users\Iago\Documents\Projects\autostride\ml\datasets\raw"
JSON_INPUT = os.path.join(ROOT_DIR, "ls.json")
# Esta é a pasta onde estão as imagens que você baixou (com os nomes estranhos)
IMAGES_SRC = os.path.join(ROOT_DIR, "images")

CLASS_MAP = {
    "boundary": 0,
    "cache": 1,
    "database": 2,
    "external_service": 3,
    "load_balancer": 4,
    "monitoring": 5,
    "security": 6,
    "service": 7,
    "user": 8,
    "fluxo_seta": 9,
}


def prepare_dataset():
    if not os.path.exists(JSON_INPUT):
        print(f"Erro: Arquivo {JSON_INPUT} não encontrado!")
        return

    with open(JSON_INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Cria estrutura de pastas YOLO
    for split in ["train", "val"]:
        os.makedirs(os.path.join(ROOT_DIR, split, "images"), exist_ok=True)
        os.makedirs(os.path.join(ROOT_DIR, split, "labels"), exist_ok=True)

    random.shuffle(data)
    split_idx = int(len(data) * 0.8)

    for i, entry in enumerate(data):
        split = "train" if i < split_idx else "val"

        # PEGA O NOME EXATO DO ARQUIVO QUE ESTÁ NO JSON
        # O Label Studio guarda assim: "/data/upload/1/2b9102cf-arch_50.png"
        raw_path = entry["data"]["image"]
        full_img_name = os.path.basename(raw_path)  # Retorna "2b9102cf-arch_50.png"
        img_name_no_ext = os.path.splitext(full_img_name)[0]

        src_img = os.path.join(IMAGES_SRC, full_img_name)
        dst_img = os.path.join(ROOT_DIR, split, "images", full_img_name)

        if os.path.exists(src_img):
            shutil.copy(src_img, dst_img)
        else:
            # Caso o arquivo no disco não tenha o hash, mas o JSON tenha
            print(f"Aviso: {full_img_name} não encontrado. Verifique a pasta images.")
            continue

        label_lines = []
        kp_list = []

        # O resto da lógica de extrair pontos e caixas continua igual
        results = entry["annotations"][0]["result"]
        for res in results:
            val = res["value"]
            if res["type"] == "rectanglelabels":
                cls_id = CLASS_MAP[val["rectanglelabels"][0]]
                xn, yn, wn, hn = (
                    (val["x"] + val["width"] / 2) / 100,
                    (val["y"] + val["height"] / 2) / 100,
                    val["width"] / 100,
                    val["height"] / 100,
                )
                label_lines.append(
                    f"{cls_id} {xn:.6f} {yn:.6f} {wn:.6f} {hn:.6f} 0 0 0 0 0 0"
                )
            elif res["type"] == "keypointlabels":
                kp_list.append({"x": val["x"] / 100, "y": val["y"] / 100})

        for j in range(0, len(kp_list), 2):
            if j + 1 < len(kp_list):
                p1, p2 = kp_list[j], kp_list[j + 1]
                xc, yc = (p1["x"] + p2["x"]) / 2, (p1["y"] + p2["y"]) / 2
                wc, hc = abs(p1["x"] - p2["x"]) + 0.02, abs(p1["y"] - p2["y"]) + 0.02
                label_lines.append(
                    f"9 {xc:.6f} {yc:.6f} {wc:.6f} {hc:.6f} {p1['x']:.6f} {p1['y']:.6f} 2 {p2['x']:.6f} {p2['y']:.6f} 2"
                )

        with open(
            os.path.join(ROOT_DIR, split, "labels", img_name_no_ext + ".txt"), "w"
        ) as f:
            f.write("\n".join(label_lines))

    print(f"\nFinalizado! Dataset organizado com os nomes originais do Label Studio.")


if __name__ == "__main__":
    prepare_dataset()

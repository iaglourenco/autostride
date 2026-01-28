"""
Script para mergear dois datasets YOLO em um único dataset combinado.
Lida com remapeamento de classes e consolidação de imagens e labels.
"""

import argparse
import os
import shutil
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from collections import OrderedDict


def load_yaml(yaml_path: str) -> dict:
    """Carrega arquivo YAML."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml(data: dict, yaml_path: str):
    """Salva dados em arquivo YAML."""
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def merge_class_names(
    dataset1_names: Dict[int, str], dataset2_names: Dict[int, str]
) -> Tuple[Dict[int, str], Dict[int, int], Dict[int, int]]:
    """
    Mescla nomes de classes de dois datasets, criando um mapeamento unificado.

    Returns:
        merged_names: Dicionário com todas as classes únicas
        dataset1_mapping: Mapeamento de IDs antigos -> novos do dataset1
        dataset2_mapping: Mapeamento de IDs antigos -> novos do dataset2
    """
    # Criar conjunto de todas as classes únicas
    all_classes = set()

    # Adicionar classes do dataset1
    for class_id, class_name in dataset1_names.items():
        all_classes.add(class_name)

    # Adicionar classes do dataset2
    for class_id, class_name in dataset2_names.items():
        all_classes.add(class_name)

    # Criar novo mapeamento ordenado alfabeticamente
    sorted_classes = sorted(all_classes)
    merged_names = {i: name for i, name in enumerate(sorted_classes)}

    # Criar mapeamento reverso para facilitar busca
    name_to_id = {name: id for id, name in merged_names.items()}

    # Criar mapeamentos de remapeamento
    dataset1_mapping = {
        old_id: name_to_id[name] for old_id, name in dataset1_names.items()
    }
    dataset2_mapping = {
        old_id: name_to_id[name] for old_id, name in dataset2_names.items()
    }

    return merged_names, dataset1_mapping, dataset2_mapping


def remap_label_file(label_path: str, class_mapping: Dict[int, int]) -> List[str]:
    """
    Lê um arquivo de label YOLO e remapeia os IDs das classes.

    Formato YOLO: class_id x_center y_center width height
    """
    remapped_lines = []

    with open(label_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            if len(parts) >= 5:
                old_class_id = int(parts[0])
                new_class_id = class_mapping.get(old_class_id, old_class_id)

                # Reconstrói a linha com o novo class_id
                remapped_line = f"{new_class_id} {' '.join(parts[1:])}"
                remapped_lines.append(remapped_line)

    return remapped_lines


def copy_and_remap_split(
    dataset_path: str,
    output_path: str,
    split: str,
    class_mapping: Dict[int, int],
    prefix: str = "",
):
    """
    Copia imagens e labels de um split (train/val) com remapeamento de classes.
    """
    images_src = Path(dataset_path) / "images" / split
    labels_src = Path(dataset_path) / "labels" / split

    images_dst = Path(output_path) / "images" / split
    labels_dst = Path(output_path) / "labels" / split

    # Criar diretórios de destino
    images_dst.mkdir(parents=True, exist_ok=True)
    labels_dst.mkdir(parents=True, exist_ok=True)

    # Verificar se os diretórios de origem existem
    if not images_src.exists():
        print(f"⚠️  Diretório não encontrado: {images_src}")
        return 0

    # Processar cada imagem
    count = 0
    for img_file in images_src.iterdir():
        if img_file.is_file():
            # Adicionar prefixo ao nome do arquivo para evitar conflitos
            new_name = f"{prefix}_{img_file.name}" if prefix else img_file.name

            # Copiar imagem
            shutil.copy2(img_file, images_dst / new_name)

            # Processar label correspondente
            label_file = labels_src / (img_file.stem + ".txt")
            if label_file.exists():
                # Remapear classes no label
                remapped_lines = remap_label_file(str(label_file), class_mapping)

                # Salvar label remapeado
                new_label_name = (
                    f"{prefix}_{label_file.name}" if prefix else label_file.name
                )
                with open(labels_dst / new_label_name, "w") as f:
                    f.write("\n".join(remapped_lines))
                    if remapped_lines:  # Adicionar newline no final se houver conteúdo
                        f.write("\n")

            count += 1

    return count


def merge_yolo_datasets(
    dataset1_path: str,
    dataset2_path: str,
    output_path: str,
    dataset1_name: str = "ds1",
    dataset2_name: str = "ds2",
):
    """
    Mescla dois datasets YOLO em um único dataset combinado.

    Args:
        dataset1_path: Caminho para o primeiro dataset
        dataset2_path: Caminho para o segundo dataset
        output_path: Caminho de saída para o dataset mesclado
        dataset1_name: Prefixo para arquivos do dataset1 (evita conflitos)
        dataset2_name: Prefixo para arquivos do dataset2 (evita conflitos)
    """
    print("🔄 Iniciando merge de datasets YOLO...")
    print(f"Dataset 1: {dataset1_path}")
    print(f"Dataset 2: {dataset2_path}")
    print(f"Output: {output_path}")
    print()

    # Carregar arquivos data.yaml
    dataset1_yaml = load_yaml(os.path.join(dataset1_path, "data.yaml"))
    dataset2_yaml = load_yaml(os.path.join(dataset2_path, "data.yaml"))

    # Extrair nomes de classes
    dataset1_names = dataset1_yaml["names"]
    dataset2_names = dataset2_yaml["names"]

    print(f"📊 Dataset 1: {len(dataset1_names)} classes")
    print(f"📊 Dataset 2: {len(dataset2_names)} classes")

    # Mesclar classes e criar mapeamentos
    merged_names, mapping1, mapping2 = merge_class_names(dataset1_names, dataset2_names)

    print(f"📊 Dataset mesclado: {len(merged_names)} classes únicas")
    print()
    print("Classes mescladas:")
    for class_id, class_name in merged_names.items():
        print(f"  {class_id}: {class_name}")
    print()

    # Criar estrutura de diretórios de saída
    output_path_obj = Path(output_path)
    output_path_obj.mkdir(parents=True, exist_ok=True)

    # Copiar e remapear splits
    for split in ["train", "val"]:
        print(f"📁 Processando split: {split}")

        # Dataset 1
        count1 = copy_and_remap_split(
            dataset1_path, output_path, split, mapping1, prefix=dataset1_name
        )
        print(f"  ✅ Dataset 1: {count1} imagens copiadas")

        # Dataset 2
        count2 = copy_and_remap_split(
            dataset2_path, output_path, split, mapping2, prefix=dataset2_name
        )
        print(f"  ✅ Dataset 2: {count2} imagens copiadas")
        print(f"  📊 Total {split}: {count1 + count2} imagens")
        print()

    # Criar novo data.yaml
    merged_yaml = {
        "path": str(output_path_obj.absolute()),
        "train": "images/train",
        "val": "images/val",
        "names": merged_names,
    }

    output_yaml_path = output_path_obj / "data.yaml"
    save_yaml(merged_yaml, str(output_yaml_path))

    print(f"✅ Dataset mesclado salvo em: {output_path}")
    print(f"✅ Arquivo data.yaml criado: {output_yaml_path}")
    print()
    print("🎉 Merge concluído com sucesso!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Mescla dois datasets YOLO em um único dataset combinado"
    )

    # Argumentos obrigatórios
    parser.add_argument(
        "--dataset1",
        type=str,
        required=True,
        help="Caminho para o primeiro dataset YOLO",
    )
    parser.add_argument(
        "--dataset2",
        type=str,
        required=True,
        help="Caminho para o segundo dataset YOLO",
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Caminho de saída para o dataset mesclado",
    )

    # Argumentos opcionais
    parser.add_argument(
        "--prefix1",
        type=str,
        default="ds1",
        help="Prefixo para arquivos do dataset1 (padrão: ds1)",
    )
    parser.add_argument(
        "--prefix2",
        type=str,
        default="ds2",
        help="Prefixo para arquivos do dataset2 (padrão: ds2)",
    )

    args = parser.parse_args()

    # Executar merge
    merge_yolo_datasets(
        args.dataset1,
        args.dataset2,
        args.output,
        dataset1_name=args.prefix1,
        dataset2_name=args.prefix2,
    )

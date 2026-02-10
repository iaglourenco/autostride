#!/usr/bin/env python3
"""
Script para remover bounding boxes de 'fluxo_seta' via API do Label Studio.
Necessário caso use o modelo de pre-labeling que adiciona essas caixas.
Mantém os keypoints intactos, remove apenas os rectanglelabels.
"""

import requests
import json

# ============ CONFIGURAÇÕES ============
LABEL_STUDIO_URL = "http://localhost:8080"  # Ajuste se necessário
API_TOKEN = "8dba6f8133bbc0846649312fdce0b9e6898005f4"  # Pegue em: Account & Settings → Access Token
PROJECT_ID = 4  # ID do seu projeto (veja na URL quando abrir o projeto)

# =======================================

headers = {"Authorization": f"Token {API_TOKEN}", "Content-Type": "application/json"}


def get_all_tasks(project_id):
    """Busca todas as tasks do projeto"""
    url = f"{LABEL_STUDIO_URL}/api/projects/{project_id}/tasks"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


def update_annotation(annotation_id, cleaned_result):
    """Atualiza uma anotação específica"""
    url = f"{LABEL_STUDIO_URL}/api/annotations/{annotation_id}"
    data = {"result": cleaned_result}
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()


def clean_fluxo_seta_boxes(tasks):
    """Remove bounding boxes de fluxo_seta das anotações"""
    removed_count = 0
    updated_annotations = 0

    for task in tasks:
        task_id = task["id"]

        # Busca anotações da task
        if "annotations" not in task or not task["annotations"]:
            continue

        for annotation in task["annotations"]:
            annotation_id = annotation["id"]
            original_result = annotation.get("result", [])

            # Filtra: remove rectanglelabels que contenham fluxo_seta
            cleaned_result = []
            boxes_removed = 0

            for item in original_result:
                # Mantém se NÃO for um rectanglelabel com fluxo_seta
                if item.get("type") == "rectanglelabels":
                    labels = item.get("value", {}).get("rectanglelabels", [])
                    if "fluxo_seta" in labels:
                        boxes_removed += 1
                        continue  # Pula este item (não adiciona ao cleaned_result)

                cleaned_result.append(item)

            # Se removeu algo, atualiza a anotação
            if boxes_removed > 0:
                print(
                    f"Task {task_id}, Annotation {annotation_id}: removendo {boxes_removed} bbox(es) de fluxo_seta"
                )
                update_annotation(annotation_id, cleaned_result)
                removed_count += boxes_removed
                updated_annotations += 1

    return removed_count, updated_annotations


def main():
    print(f"Conectando ao Label Studio em {LABEL_STUDIO_URL}...")
    print(f"Buscando tasks do projeto {PROJECT_ID}...\n")

    try:
        tasks = get_all_tasks(PROJECT_ID)
        print(f"✓ Encontradas {len(tasks)} tasks\n")

        print("Removendo bounding boxes de 'fluxo_seta'...")
        removed, updated = clean_fluxo_seta_boxes(tasks)

        print(f"\n{'='*50}")
        print(f"✓ Concluído!")
        print(f"  - {removed} bounding box(es) removido(s)")
        print(f"  - {updated} anotação(ões) atualizada(s)")
        print(f"{'='*50}\n")

    except requests.exceptions.RequestException as e:
        print(f"\n✗ Erro na API: {e}")
        print("\nVerifique:")
        print("  1. Label Studio está rodando?")
        print("  2. URL está correta?")
        print("  3. Token de API está válido?")
        print("  4. PROJECT_ID está correto?")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  REMOVEDOR DE BBOXES FLUXO_SETA")
    print("=" * 50 + "\n")
    main()

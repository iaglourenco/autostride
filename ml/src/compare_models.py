import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any


def analyze_model(model_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a single model's performance from results.csv"""
    results_csv = model_path / "results.csv"

    if not results_csv.exists():
        return None

    df = pd.read_csv(results_csv)

    # Get best metrics
    best_epoch = df["metrics/mAP50-95(B)"].idxmax()

    return {
        "name": model_path.name,
        "path": str(model_path),
        "total_epochs": len(df),
        "best_epoch": int(best_epoch) + 1,  # type: ignore
        "best_mAP50-95": float(df.loc[best_epoch, "metrics/mAP50-95(B)"]),  # type: ignore
        "best_mAP50": float(df.loc[best_epoch, "metrics/mAP50(B)"]),  # type: ignore
        "best_precision": float(df.loc[best_epoch, "metrics/precision(B)"]),  # type: ignore
        "best_recall": float(df.loc[best_epoch, "metrics/recall(B)"]),  # type: ignore
        "final_mAP50-95": float(df.iloc[-1]["metrics/mAP50-95(B)"]),  # type: ignore
        "final_mAP50": float(df.iloc[-1]["metrics/mAP50(B)"]),  # type: ignore
    }


def compare_models(runs_dir: Path) -> None:
    """Compare all models in the runs directory"""
    detect_dir = runs_dir / "detect"

    if not detect_dir.exists():
        print(f"❌ Directory not found: {detect_dir}")
        return

    # Find all model directories
    model_dirs = [d for d in detect_dir.iterdir() if d.is_dir()]

    if not model_dirs:
        print(f"❌ No models found in {detect_dir}")
        return

    # Analyze each model
    models: List[Dict[str, Any]] = []
    for model_dir in model_dirs:
        result = analyze_model(model_dir)
        if result:
            models.append(result)

    if not models:
        print("❌ No valid model results found")
        return

    # Sort by best mAP50-95
    models.sort(key=lambda x: x["best_mAP50-95"], reverse=True)

    # Display results
    print("=" * 100)
    print("🏆 MODEL COMPARISON RESULTS")
    print("=" * 100)
    print()

    for i, model in enumerate(models, 1):
        rank_emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        print(f"{rank_emoji} {model['name']}")
        print(f"   Epochs: {model['total_epochs']}")
        print(f"   Best Epoch: {model['best_epoch']}")
        print(f"   Best mAP50-95: {model['best_mAP50-95']:.4f}")
        print(f"   Best mAP50: {model['best_mAP50']:.4f}")
        print(f"   Best Precision: {model['best_precision']:.4f}")
        print(f"   Best Recall: {model['best_recall']:.4f}")
        print(f"   Final mAP50-95: {model['final_mAP50-95']:.4f}")
        print(f"   Path: {model['path']}")
        print()

    # Best model summary
    best = models[0]
    print("=" * 100)
    print("✨ BEST MODEL")
    print("=" * 100)
    print(f"Model: {best['name']}")
    print(f"Best mAP50-95: {best['best_mAP50-95']:.4f} (epoch {best['best_epoch']})")
    print(f"Weights: {best['path']}/weights/best.pt")
    print("=" * 100)


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    runs_dir = script_dir.parent / "runs"

    compare_models(runs_dir)

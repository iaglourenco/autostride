import argparse
from pathlib import Path
from ultralytics.models import YOLO


def get_experiment_name(
    model_name: str, dataset_path: str, experiments_dir: Path
) -> str:
    """Generate experiment name with auto-incrementing version number."""
    model_base = model_name.replace(".pt", "")
    dataset_name = Path(dataset_path).parent.name

    # Find existing experiments with same model and dataset
    pattern = f"{model_base}_{dataset_name}_v"
    existing = [
        d.name
        for d in experiments_dir.iterdir()
        if d.is_dir() and d.name.startswith(pattern)
    ]

    if not existing:
        version = 1
    else:
        # Extract version numbers and get max
        versions = []
        for exp in existing:
            try:
                v = int(exp.split("_v")[-1])
                versions.append(v)
            except ValueError:
                continue
        version = max(versions) + 1 if versions else 1

    return f"{model_base}_{dataset_name}_v{version}"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLO model")
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of epochs to train (default: 100)",
    )
    parser.add_argument(
        "--data",
        type=str,
        required=True,
        help="Path to the dataset YAML file",
    )
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="The YOLO model configuration file",
    )

    args = parser.parse_args()

    # Define absolute path for experiments
    script_dir = Path(__file__).parent
    experiments_dir = script_dir.parent / "runs" / "detect"
    experiments_dir.mkdir(parents=True, exist_ok=True)

    # Load model
    model = YOLO("models/" + args.model)

    # Generate experiment name
    experiment_name = get_experiment_name(args.model, args.data, experiments_dir)

    print("Starting training from scratch...")
    print(f"Training dataset: {args.data}")
    print(f"Number of epochs: {args.epochs}")
    print(f"Model configuration: {args.model}")
    print(f"Experiment name: {experiment_name}")
    print("-" * 80)

    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=640,
        batch=24,
        name=experiment_name,
        project=str(experiments_dir),  # Nome do projeto
    )

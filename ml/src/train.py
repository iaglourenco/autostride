import argparse
from pathlib import Path
from ultralytics.models import YOLO


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLO model")
    parser.add_argument(
        "--resume", action="store_true", help="Resume training from last checkpoint"
    )
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

    if args.resume:
        model = YOLO(
            str(experiments_dir / args.model.split(".")[0] / "weights" / "last.pt")
        )
    else:
        if not args.model:
            raise ValueError("Model path must be specified when not resuming.")
        model = YOLO("models/" + args.model)

    if args.resume:
        print("Resuming training from last checkpoint...")
        print(f"Training dataset: {args.data}")
        print(
            f"Model configuration: {experiments_dir / args.model.split('.')[0] / 'weights' / 'last.pt'}"
        )
        print("-" * 80)
        results = model.train(
            data=args.data,
            resume=args.resume,
            project=str(experiments_dir),
            name=args.model.split(".")[0],
        )

    else:
        print("Starting training from scratch...")
        print(f"Training dataset: {args.data}")
        print(f"Number of epochs: {args.epochs}")
        print(f"Model configuration: {args.model}")
        print("-" * 80)
        results = model.train(
            data=args.data,
            epochs=args.epochs,
            imgsz=640,
            batch=0.95,
            name=args.model.split(".")[0],
            project=str(experiments_dir),
        )

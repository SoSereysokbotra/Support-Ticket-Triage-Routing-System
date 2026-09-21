import argparse
import sys
from pathlib import Path
from typing import Optional, Union

# Ensure UTF-8 output on Windows to prevent UnicodeEncodeError with emoji prints
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


def export_distilbert_to_onnx(
    model_dir: Union[str, Path],
    output_path: Optional[Union[str, Path]] = None,
    opset_version: int = 18,
) -> Path:
    """
    Exports a trained Hugging Face DistilBERT model to an optimized ONNX computational graph.
    Supports dynamic batch sizes and dynamic token sequence lengths.

    Args:
        model_dir: Directory containing the PyTorch model checkpoint (config.json, weights).
        output_path: Target .onnx output file path. Defaults to model_dir / "model.onnx".
        opset_version: Target ONNX operator set version (default 17).

    Returns:
        Path to the generated .onnx file.
    """
    model_path = Path(model_dir)
    if not model_path.exists():
        raise FileNotFoundError(f"Model directory does not exist: {model_path}")

    target_output = Path(output_path) if output_path else model_path / "model.onnx"
    target_output.parent.mkdir(parents=True, exist_ok=True)

    print(f"[ONNX Exporter] Loading PyTorch model & tokenizer from: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(str(model_path))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
    model.eval()

    # Create representative dummy inputs
    sample_text = "Customer unable to access billing portal to update payment method."
    inputs = tokenizer(
        sample_text,
        return_tensors="pt",
        truncation=True,
        max_length=256,
        padding=True,
    )
    input_ids = inputs["input_ids"]
    attention_mask = inputs["attention_mask"]

    # Define dynamic axes for variable batch sizes and sequence lengths
    dynamic_axes = {
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "logits": {0: "batch_size"},
    }

    print(f"[ONNX Exporter] Exporting computational graph to: {target_output} (opset {opset_version})...")
    with torch.no_grad():
        torch.onnx.export(
            model,
            (input_ids, attention_mask),
            str(target_output),
            input_names=["input_ids", "attention_mask"],
            output_names=["logits"],
            dynamic_axes=dynamic_axes,
            opset_version=opset_version,
            do_constant_folding=True,
        )

    # Validate exported ONNX graph integrity
    try:
        import onnx

        onnx_model = onnx.load(str(target_output))
        onnx.checker.check_model(onnx_model)
        print("[ONNX Exporter] ONNX graph structure validated successfully with onnx.checker.")
    except ImportError:
        print("[ONNX Exporter] onnx package not found; skipped onnx.checker validation.")

    # Validate numerical parity against PyTorch reference
    try:
        import onnxruntime as ort

        session = ort.InferenceSession(
            str(target_output),
            providers=["CPUExecutionProvider"],
        )
        ort_inputs = {
            "input_ids": input_ids.cpu().numpy(),
            "attention_mask": attention_mask.cpu().numpy(),
        }
        ort_logits = session.run(["logits"], ort_inputs)[0]

        with torch.no_grad():
            pt_logits = model(input_ids, attention_mask=attention_mask).logits.cpu().numpy()

        max_abs_diff = float(np.max(np.abs(pt_logits - ort_logits)))
        print(f"[ONNX Exporter] Numerical parity check: Max absolute logit difference = {max_abs_diff:.6e}")
        if max_abs_diff > 1e-3:
            print(f"[ONNX Exporter] WARNING: Max difference {max_abs_diff:.6e} exceeds expected tolerance 1e-3.")
        else:
            print("[ONNX Exporter] Numerical parity verified within strict tolerance (< 1e-3).")
    except ImportError:
        print("[ONNX Exporter] onnxruntime not found; skipped runtime parity validation.")

    file_size_mb = target_output.stat().st_size / (1024 * 1024)
    print(f"[ONNX Exporter] Export complete: {target_output} ({file_size_mb:.2f} MB)")
    return target_output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Hugging Face DistilBERT model to ONNX format.")
    parser.add_argument(
        "--model-dir",
        type=str,
        default="models/distilbert_v0",
        help="Directory containing PyTorch model checkpoint.",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Target .onnx file path. Defaults to <model-dir>/model.onnx",
    )
    parser.add_argument(
        "--opset",
        type=int,
        default=18,
        help="ONNX Opset version (default: 18).",
    )
    args = parser.parse_args()

    export_distilbert_to_onnx(
        model_dir=args.model_dir,
        output_path=args.output_path,
        opset_version=args.opset,
    )

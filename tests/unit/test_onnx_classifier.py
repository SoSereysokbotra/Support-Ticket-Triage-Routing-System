from pathlib import Path

import pytest

from src.domain.entities.category import TicketCategory
from src.domain.value_objects.prediction_result import PredictionResult
from src.infrastructure.models.distilbert_classifier import DistilBertTicketClassifier
from src.infrastructure.models.onnx_distilbert_classifier import OnnxDistilBertClassifier

MODEL_DIR = Path("models/distilbert_v0")


@pytest.fixture
def onnx_classifier():
    if not (MODEL_DIR / "model.onnx").exists():
        pytest.skip("models/distilbert_v0/model.onnx not present. Skipping ONNX tests.")
    return OnnxDistilBertClassifier(
        model_path_or_dir=MODEL_DIR,
        model_version="distilbert-onnx-test",
    )


def test_onnx_classifier_initialization_and_metadata(onnx_classifier):
    assert onnx_classifier.model_version == "distilbert-onnx-test"
    assert onnx_classifier.device == "cpu-onnxruntime"


def test_onnx_classifier_single_prediction(onnx_classifier):
    text = "The VPN connection to the corporate server fails with error 403"
    result = onnx_classifier.predict(text)

    assert isinstance(result, PredictionResult)
    assert result.predicted_category in [cat for cat in TicketCategory]
    assert 0.0 <= result.confidence <= 1.0
    assert result.latency_ms > 0.0
    assert result.model_version == "distilbert-onnx-test"

    # Softmax probabilities should sum to approximately 1.0
    total_prob = sum(result.probabilities.values())
    assert abs(total_prob - 1.0) < 1e-3


def test_onnx_classifier_batch_prediction(onnx_classifier):
    texts = [
        "Printer in building B is out of paper and jammed",
        "Cannot log in to email account, password rejected",
        "Requesting invoice for monthly SaaS subscription",
    ]
    results = onnx_classifier.predict_batch(texts)

    assert len(results) == len(texts)
    for res in results:
        assert isinstance(res, PredictionResult)
        assert 0.0 <= res.confidence <= 1.0
        assert res.latency_ms > 0.0


def test_onnx_classifier_empty_batch(onnx_classifier):
    results = onnx_classifier.predict_batch([])
    assert results == []


def test_onnx_classifier_dynamic_length(onnx_classifier):
    # Short text (single word)
    short_res = onnx_classifier.predict("Help")
    assert isinstance(short_res, PredictionResult)

    # Long text (exceeding typical sequence length, should be truncated)
    long_text = "Critical system failure. " * 100
    long_res = onnx_classifier.predict(long_text)
    assert isinstance(long_res, PredictionResult)


def test_onnx_parity_with_pytorch(onnx_classifier):
    if not (MODEL_DIR / "config.json").exists():
        pytest.skip("PyTorch weights not present.")

    pt_clf = DistilBertTicketClassifier(
        model_path_or_name=MODEL_DIR,
        model_version="distilbert-pt-test",
        device="cpu",
    )

    test_queries = [
        "Laptop screen is flickering and won't turn on",
        "Need refund for duplicate charge on my credit card",
        "Wifi router is flashing orange and connection dropped",
        "Cannot reset two-factor authentication token",
    ]

    for q in test_queries:
        pt_res = pt_clf.predict(q)
        onnx_res = onnx_classifier.predict(q)

        # Classification decision must agree
        assert pt_res.predicted_category == onnx_res.predicted_category

        # Confidence delta must be within tight tolerance
        assert abs(pt_res.confidence - onnx_res.confidence) < 1e-3


def test_onnx_missing_file_raises_error(tmp_path):
    fake_dir = tmp_path / "non_existent_model"
    fake_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        OnnxDistilBertClassifier(model_path_or_dir=fake_dir)

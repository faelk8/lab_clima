"""Smoke SDP executado apenas no serviço Docker configurado."""

import os

import pytest


@pytest.mark.skipif(os.getenv("CLIMATEWATCH_SDP_SMOKE") != "1", reason="requer Docker SDP validado")
def test_sdp_runtime_is_opt_in() -> None:
    """Mantém o smoke opt-in para não baixar imagens incidentalmente."""
    import pyspark.pipelines as dp

    assert dp is not None

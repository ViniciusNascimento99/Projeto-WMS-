"""O contrato (openapi.yaml) precisa ser válido e bater com a API real."""
from pathlib import Path

import yaml
from openapi_spec_validator import validate

from main import app

RAIZ = Path(__file__).resolve().parents[2]
spec = yaml.safe_load((RAIZ / "openapi.yaml").read_text(encoding="utf-8"))


def test_openapi_yaml_e_valido():
    validate(spec)


def test_rotas_da_api_batem_com_o_contrato():
    no_contrato = {
        (metodo.upper(), "/api/v1" + caminho)
        for caminho, ops in spec["paths"].items()
        for metodo in ops
    }
    na_api = {
        (metodo.upper(), caminho)
        for caminho, ops in app.openapi()["paths"].items()
        if caminho.startswith("/api/v1")
        for metodo in ops
    }
    assert no_contrato == na_api

import pytest

from src.domain.errors import DomainError
from src.domain.models import PickingItem, PickingOrder


def ordem():
    return PickingOrder("K1", "PED-1", [
        PickingItem("P", "A-01", 10),
        PickingItem("Q", "A-02", 5),
    ])


def test_status_evolui_ate_separada():
    o = ordem()
    o.confirm("P", 10)
    assert o.status == "EM_SEPARACAO"
    o.confirm("Q", 5)
    assert o.status == "SEPARADA"


def test_quantidade_confirmada_deve_ser_a_do_picking():
    with pytest.raises(DomainError) as e:
        ordem().confirm("P", 9)
    assert e.value.code == "QUANTITY_MISMATCH"


def test_nao_confirma_duas_vezes():
    o = ordem()
    o.confirm("P", 10)
    with pytest.raises(DomainError) as e:
        o.confirm("P", 10)
    assert e.value.code == "ALREADY_PICKED"


def test_produto_fora_da_ordem():
    with pytest.raises(DomainError) as e:
        ordem().confirm("X", 1)
    assert e.value.status == 404

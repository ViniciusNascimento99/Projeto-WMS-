import pytest

from src.domain.errors import DomainError
from src.domain.models import Receipt, ReceiptItem


def novo(qtd=10):
    return Receipt("R1", "C1", None, [ReceiptItem("P", qtd)])


def test_conferencia_sem_divergencia():
    r = novo()
    assert r.conference({"P": 10}) is False
    assert r.status == "CONFERIDA"


def test_conferencia_com_divergencia():
    r = novo()
    assert r.conference({"P": 8}) is True
    assert r.status == "COM_DIVERGENCIA"
    assert r.items[0].counted_quantity == 8


def test_nao_confere_duas_vezes():
    r = novo()
    r.conference({"P": 10})
    with pytest.raises(DomainError) as e:
        r.conference({"P": 10})
    assert e.value.code == "INVALID_RECEIPT_STATE"


def test_produtos_da_conferencia_devem_bater_com_o_recebimento():
    with pytest.raises(DomainError) as e:
        novo().conference({"OUTRO": 10})
    assert e.value.code == "CONFERENCE_ITEMS_MISMATCH"

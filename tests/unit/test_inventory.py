import pytest

from src.domain.errors import DomainError
from src.domain.models import Address, Inventory


def estoque_com(qtd=100, endereco="A-01", capacidade=1000):
    inv = Inventory()
    inv.receive("P", qtd)
    inv.store("P", Address(endereco, capacidade), qtd)
    return inv


def test_nao_guarda_o_que_nao_foi_recebido():
    inv = Inventory()
    with pytest.raises(DomainError) as e:
        inv.store("P", Address("A-01", 100), 10)
    assert e.value.code == "NOT_RECEIVED"


def test_nao_ultrapassa_a_capacidade_do_endereco():
    inv = Inventory()
    inv.receive("P", 500)
    with pytest.raises(DomainError) as e:
        inv.store("P", Address("A-01", 100), 500)
    assert e.value.code == "ADDRESS_CAPACITY_EXCEEDED"


def test_endereco_inativo_nao_recebe():
    inv = Inventory()
    inv.receive("P", 10)
    with pytest.raises(DomainError) as e:
        inv.store("P", Address("A-01", 100, active=False), 10)
    assert e.value.code == "ADDRESS_INACTIVE"


def test_saldo_e_consolidado_por_produto_e_endereco():
    inv = Inventory()
    inv.receive("P", 30)
    inv.store("P", Address("A-01", 100), 10)
    inv.store("P", Address("A-01", 100), 20)
    assert inv.lines() == [{"productId": "P", "addressCode": "A-01", "quantity": 30}]


def test_reserva_impede_segundo_picking_do_mesmo_saldo():
    inv = estoque_com(10)
    inv.reserve({"P": 10})
    with pytest.raises(DomainError) as e:
        inv.reserve({"P": 1})
    assert e.value.code == "INSUFFICIENT_STOCK"


def test_reserva_e_tudo_ou_nada():
    inv = estoque_com(10)
    with pytest.raises(DomainError):
        inv.reserve({"P": 5, "Q": 1})  # Q não existe
    assert inv.available("P") == 10  # nada ficou reservado


def test_reserva_usa_varios_enderecos():
    inv = Inventory()
    inv.receive("P", 15)
    inv.store("P", Address("A-01", 100), 10)
    inv.store("P", Address("B-01", 100), 5)
    plano = inv.reserve({"P": 12})
    assert plano["P"] == [("A-01", 10), ("B-01", 2)]


def test_separacao_baixa_saldo_e_registra_saida():
    inv = estoque_com(10)
    inv.reserve({"P": 4})
    saldo = inv.pick("P", "A-01", 4)
    assert saldo == 6
    assert [m.type for m in inv.movements_of("P")] == ["ENTRADA", "SAIDA"]

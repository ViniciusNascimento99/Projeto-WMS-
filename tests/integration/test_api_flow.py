from tests.conftest import API, criar_endereco, criar_produto, estoque_pronto, receber_e_conferir


def picking(client, order="PED-1", sku="SKU-1", qtd=10):
    return client.post(f"{API}/picking", json={
        "orderId": order, "items": [{"productId": sku, "quantity": qtd}]})


def separar(client, picking_id, sku="SKU-1", qtd=10):
    return client.post(f"{API}/picking/{picking_id}/pick", json={"productId": sku, "quantity": qtd})


def fluxo_ate_embalado(client, order="PED-1", qtd=10):
    p = picking(client, order, qtd=qtd).json()
    separar(client, p["id"], qtd=qtd)
    r = client.post(f"{API}/packing", json={"orderId": order, "volumes": 1})
    assert r.status_code == 201, r.text


# ---------------------------------------------------------------- fluxo
def test_fluxo_completo_zera_o_estoque_e_gera_historico(client, eventos):
    estoque_pronto(client, quantidade=10)
    fluxo_ate_embalado(client, qtd=10)

    r = client.post(f"{API}/shipments", json={"orderIds": ["PED-1"], "destination": "Recife - PE"})
    assert r.status_code == 201
    assert r.json()["status"] == "EXPEDIDA"
    assert r.json()["shippedAt"] is not None

    assert client.get(f"{API}/inventory").json() == []
    tipos = [m["type"] for m in client.get(f"{API}/inventory/SKU-1/movements").json()]
    assert tipos == ["ENTRADA", "SAIDA"]

    assert [e["event"] for e in eventos] == [
        "MercadoriaRecebida", "ProdutoArmazenado", "EstoqueAtualizado",
        "PickingCriado", "EstoqueAtualizado", "PedidoSeparado",
        "PedidoEmbalado", "CargaExpedida",
    ]


def test_consulta_de_expedicao(client):
    estoque_pronto(client, quantidade=10)
    fluxo_ate_embalado(client)
    sid = client.post(f"{API}/shipments", json={"orderIds": ["PED-1"], "destination": "X"}).json()["shipmentId"]
    assert client.get(f"{API}/shipments/{sid}").status_code == 200
    assert client.get(f"{API}/shipments/nao-existe").status_code == 404


# ---------------------------------------------------------------- estoque
def test_alocacao_exige_mercadoria_recebida_e_conferida(client):
    criar_produto(client)
    criar_endereco(client)
    r = client.post(f"{API}/allocations", json={"productId": "SKU-1", "addressCode": "A-01", "quantity": 5})
    assert r.status_code == 409
    assert r.json()["code"] == "NOT_RECEIVED"


def test_recebimento_com_divergencia_nao_libera_estoque(client):
    criar_produto(client)
    criar_endereco(client)
    r = receber_e_conferir(client, quantidade=10, contado=8)
    assert r["status"] == "COM_DIVERGENCIA"
    r = client.post(f"{API}/allocations", json={"productId": "SKU-1", "addressCode": "A-01", "quantity": 8})
    assert r.status_code == 409


def test_alocacao_respeita_capacidade(client):
    criar_produto(client)
    criar_endereco(client, capacity=5)
    receber_e_conferir(client, quantidade=10)
    r = client.post(f"{API}/allocations", json={"productId": "SKU-1", "addressCode": "A-01", "quantity": 10})
    assert r.status_code == 409
    assert r.json()["code"] == "ADDRESS_CAPACITY_EXCEEDED"


def test_estoque_consolida_alocacoes_no_mesmo_endereco(client):
    criar_produto(client)
    criar_endereco(client)
    receber_e_conferir(client, quantidade=30)
    for qtd in (10, 20):
        client.post(f"{API}/allocations", json={"productId": "SKU-1", "addressCode": "A-01", "quantity": qtd})
    assert client.get(f"{API}/inventory").json() == [
        {"productId": "SKU-1", "addressCode": "A-01", "quantity": 30}]


# ---------------------------------------------------------------- picking
def test_picking_sem_saldo_suficiente_e_409(client):
    estoque_pronto(client, quantidade=10)
    r = picking(client, qtd=11)
    assert r.status_code == 409
    assert r.json()["code"] == "INSUFFICIENT_STOCK"


def test_reserva_bloqueia_segundo_picking_do_mesmo_saldo(client):
    estoque_pronto(client, quantidade=10)
    assert picking(client, "PED-1", qtd=10).status_code == 201
    r = picking(client, "PED-2", qtd=1)
    assert r.status_code == 409


def test_separacao_baixa_o_saldo(client):
    estoque_pronto(client, quantidade=10)
    p = picking(client, qtd=4).json()
    assert client.get(f"{API}/inventory").json()[0]["quantity"] == 10  # reservado, ainda fisico
    separar(client, p["id"], qtd=4)
    assert client.get(f"{API}/inventory").json()[0]["quantity"] == 6


def test_nao_cria_dois_pickings_para_o_mesmo_pedido(client):
    estoque_pronto(client, quantidade=10)
    picking(client, "PED-1", qtd=2)
    assert picking(client, "PED-1", qtd=2).status_code == 409


# ---------------------------------------------------------------- packing / expedição
def test_nao_embala_pedido_nao_separado(client):
    estoque_pronto(client, quantidade=10)
    picking(client, "PED-1", qtd=2)
    r = client.post(f"{API}/packing", json={"orderId": "PED-1"})
    assert r.status_code == 409
    assert r.json()["code"] == "ORDER_NOT_PICKED"


def test_nao_embala_o_mesmo_pedido_duas_vezes(client):
    estoque_pronto(client, quantidade=10)
    fluxo_ate_embalado(client)
    r = client.post(f"{API}/packing", json={"orderId": "PED-1"})
    assert r.status_code == 409
    assert r.json()["code"] == "ORDER_ALREADY_PACKED"


def test_nao_expede_pedido_nao_embalado(client):
    r = client.post(f"{API}/shipments", json={"orderIds": ["NAO-EXISTE"], "destination": "X"})
    assert r.status_code == 409
    assert r.json()["code"] == "ORDER_NOT_PACKED"


def test_nao_expede_o_mesmo_pedido_duas_vezes(client):
    estoque_pronto(client, quantidade=10)
    fluxo_ate_embalado(client)
    body = {"orderIds": ["PED-1"], "destination": "X"}
    assert client.post(f"{API}/shipments", json=body).status_code == 201
    r = client.post(f"{API}/shipments", json=body)
    assert r.status_code == 409
    assert r.json()["code"] == "ORDER_ALREADY_SHIPPED"


# ---------------------------------------------------------------- cadastros e erros
def test_sku_duplicado_e_409(client):
    criar_produto(client)
    r = client.post(f"{API}/products", json={"sku": "SKU-1", "description": "x", "unit": "UN"})
    assert r.status_code == 409


def test_recebimento_de_produto_inexistente_e_404(client):
    r = client.post(f"{API}/receipts", json={
        "cargoId": "C", "items": [{"productId": "NAO", "expectedQuantity": 1}]})
    assert r.status_code == 404


def test_validacao_devolve_422_no_formato_do_contrato(client):
    r = client.post(f"{API}/products", json={})
    assert r.status_code == 422
    assert set(r.json()) == {"code", "message"}
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_capacidade_zero_e_quantidade_negativa_sao_rejeitadas(client):
    assert client.post(f"{API}/addresses", json={"code": "A", "capacity": 0}).status_code == 422
    assert client.post(f"{API}/receipts", json={
        "cargoId": "C", "items": [{"productId": "P", "expectedQuantity": -1}]}).status_code == 422


def test_erro_404_tem_o_formato_do_contrato(client):
    r = client.get(f"{API}/products/nao-existe")
    assert r.status_code == 404
    assert set(r.json()) == {"code", "message"}

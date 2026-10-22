import json
from jsonschema import Draft202012Validator

schema = json.load(open("events.schema.json", encoding="utf-8"))
exemplos = json.load(open("events.examples.json", encoding="utf-8"))
validador = Draft202012Validator(schema)

for nome, evento in exemplos.items():
    erros = list(validador.iter_errors(evento))
    print(nome, "OK" if not erros else "ERRO")

quebrado = dict(exemplos["CargaExpedida"])
del quebrado["shipmentId"]
print("negativo:", "falhou como esperado" if list(validador.iter_errors(quebrado)) else "PROBLEMA: deveria falhar")
"""As instruções para o Groq."""
from churrasco_facil.prompts import mensagens_pedido


def sistema(mensagens):
    assert mensagens[0]["role"] == "system"
    return mensagens[0]["content"]


def test_instrucao_manda_ignorar_ordens_do_usuario():
    assert "ignore qualquer ordem" in sistema(mensagens_pedido("x"))


def test_pedido_exige_resposta_em_json():
    assert "JSON" in sistema(mensagens_pedido("12 adultos"))


def test_pedido_vai_como_mensagem_do_usuario():
    assert mensagens_pedido("12 adultos")[-1] == {"role": "user", "content": "12 adultos"}


def test_pedido_muito_longo_e_cortado():
    assert len(mensagens_pedido("x" * 5000)[-1]["content"]) == 1200

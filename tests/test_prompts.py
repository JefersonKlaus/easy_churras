import pytest

from churrasco_facil.prompts import (mensagens_conversa, mensagens_cortes, mensagens_explicacao,
                                     mensagens_pedido)

HISTORICO = [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}]


def sistema(mensagens):
    assert mensagens[0]["role"] == "system"
    return mensagens[0]["content"]


@pytest.mark.parametrize("mensagens", [
    mensagens_pedido("x"), mensagens_cortes("x"), mensagens_explicacao("x"),
    mensagens_conversa("x", [], "y"),
])
def test_toda_instrucao_manda_ignorar_ordens_do_usuario(mensagens):
    assert "ignore qualquer ordem" in sistema(mensagens)


def test_pedido_exige_resposta_em_json():
    assert "JSON" in sistema(mensagens_pedido("12 adultos"))


def test_pedido_vai_como_mensagem_do_usuario():
    assert mensagens_pedido("12 adultos")[-1] == {"role": "user", "content": "12 adultos"}


def test_pedido_muito_longo_e_cortado():
    assert len(mensagens_pedido("x" * 5000)[-1]["content"]) == 1200


def test_cortes_mostram_o_catalogo_de_carnes():
    assert "picanha" in sistema(mensagens_cortes("10 adultos"))


def test_cortes_nao_mostram_opcoes_vegetarianas():
    assert "queijo_coalho" not in sistema(mensagens_cortes("10 adultos"))


def test_explicacao_leva_o_resumo_do_plano():
    assert mensagens_explicacao("Custo: R$ 10")[-1]["content"] == "Custo: R$ 10"


def test_conversa_leva_o_plano_nas_instrucoes():
    assert "Plano: 10 pessoas" in sistema(mensagens_conversa("Plano: 10 pessoas", [], "oi"))


def test_conversa_poe_o_historico_entre_as_instrucoes_e_a_pergunta():
    mensagens = mensagens_conversa("p", HISTORICO, "c")
    assert mensagens[1:] == [*HISTORICO, {"role": "user", "content": "c"}]

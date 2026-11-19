"""Aba Carnes: as melhores carnes da opção já marcadas, para a pessoa trocar à vontade."""
import pytest
from tela import (achar, digitar, fixos, parte_que_rola, pelo_rotulo_de_acessibilidade, textos,
                  tocar)

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.dinheiro import formatar_reais
from churrasco_facil.lista_compras import formatar_peso, formatar_quantidade

pytestmark = pytest.mark.usefixtures("plano_aberto")


def caixa(pagina, nome):
    """A caixa de marcar de uma carne."""
    return pelo_rotulo_de_acessibilidade(pagina, f"Levar {nome}")


def marcar(pagina, nome, valor=True):
    digitar(caixa(pagina, nome), valor)


def ids_comprados(app):
    return [i.produto.id for i in app.plano.compras.carnes]


# ---------------------------------------------------------------- a melhor escolha, já marcada

def test_melhores_carnes_da_opcao_ja_vem_marcadas(pagina, plano):
    assert all(caixa(pagina, i.produto.nome).value for i in plano.compras.carnes)


def test_carne_marcada_aparece_com_a_quantidade(pagina, plano):
    item = plano.compras.carnes[0]
    assert formatar_quantidade(item) in textos(pagina)


def test_as_outras_carnes_aparecem_para_marcar(pagina):
    assert caixa(pagina, "Costela bovina").value is False


def test_resumo_mostra_o_total_o_valor_por_pessoa_e_a_carne(pagina, plano):
    assert formatar_reais(plano.custo_total) in textos(pagina)
    assert "total com carnes, bebidas e carvão" in textos(pagina)
    assert (f"{formatar_reais(plano.custo_por_pessoa)} por pessoa · "
            f"{formatar_peso(plano.gramas_de_carne)} de carne") in textos(pagina)


# ---------------------------------------------------------------- trocar as carnes

def test_marcar_uma_carne_poe_na_compra_e_no_custo(app, pagina, plano):
    marcar(pagina, "Coração de frango")
    assert "coracao_frango" in ids_comprados(app) and app.plano.custo_total > plano.custo_total
    assert formatar_reais(app.plano.custo_total) in textos(pagina)      # o resumo acompanha


def test_carne_marcada_vai_para_os_horarios(app, pagina):
    marcar(pagina, "Coração de frango")
    assert any(e.titulo == "Na grelha: Coração de frango" for e in app.plano.cronograma)


def test_desmarcar_tira_a_carne_da_compra(app, pagina):
    marcar(pagina, "Linguiça toscana", False)
    assert "linguica_toscana" not in ids_comprados(app)


def test_nao_deixa_desmarcar_a_ultima_carne(app, pagina):
    for nome in [i.produto.nome for i in app.plano.compras.carnes]:
        marcar(pagina, nome, False)
    assert len(ids_comprados(app)) == 1
    assert "Deixe pelo menos uma carne marcada." in textos(pagina)


def test_trocar_as_carnes_deixa_o_plano_por_salvar(app, pagina):
    app.salvar_plano()
    app.ir_carnes()
    marcar(pagina, "Coração de frango")
    assert app.salvo is False and "Salvar" in fixos(pagina)


# ---------------------------------------------------------------- dicas da escolha

def test_dicas_ficam_escondidas_ate_tocar(pagina):
    assert f"Combina com: {CORTES['picanha'].combina_com}" not in textos(pagina)


def test_tocar_na_carne_mostra_o_que_combina_e_como_escolher(pagina):
    tocar(pagina, "Picanha")
    assert f"Combina com: {CORTES['picanha'].combina_com}" in textos(pagina)
    assert f"Na hora de comprar: {CORTES['picanha'].como_escolher}" in textos(pagina)


def test_dicas_da_escolha_nao_falam_de_preparo_nem_de_como_pedir(pagina):
    # como preparar fica nos Horários; como pedir ao açougueiro, nas Compras
    picanha = CORTES["picanha"]
    tocar(pagina, "Picanha")
    assert not any(dica in texto for texto in textos(pagina)
                   for dica in (picanha.preparo, picanha.ponto, picanha.como_pedir))


def test_o_vazio_aparece_para_marcar(pagina):
    assert caixa(pagina, "Vazio").value is False


def test_vegetarianos_veem_a_grelha_deles(pagina):
    # o fixture tem 1 vegetariano
    assert "Para quem não come carne" in textos(pagina)


# ---------------------------------------------------------------- alerta: falta, certa ou demais

def alerta(pagina):
    """O texto e a cor da faixa de alerta no alto da tela (fixa, fora da parte que rola)."""
    texto = next(t for t in fixos(pagina) if t.startswith(("Falta", "Carne")))
    return texto, achar(pagina, texto).color


def cores():
    from churrasco_facil.telas import tema  # já carregado com o Flet de mentira
    return tema


def test_melhor_escolha_fica_verde(pagina):
    texto, cor = alerta(pagina)
    assert texto.startswith("Carne certa") and cor == cores().CERTO


def test_desmarcar_carne_demais_fica_vermelho_no_alto(pagina):
    marcar(pagina, "Picanha", False)
    texto, cor = alerta(pagina)
    assert texto.startswith("Falta carne") and cor == cores().PERIGO


def test_um_pouco_a_mais_fica_verde(pagina):
    marcar(pagina, "Coração de frango")            # 500 g a mais: tudo bem
    texto, cor = alerta(pagina)
    assert "Um pouco mais que o indicado" in texto and cor == cores().CERTO


def test_carne_demais_fica_amarelo_no_alto(pagina):
    for nome in ("Costela bovina", "Maminha"):
        marcar(pagina, nome)
    texto, cor = alerta(pagina)
    assert texto.startswith("Carne demais") and cor == cores().ATENCAO


def test_volta_ao_verde_quando_a_carne_fica_certa(pagina):
    marcar(pagina, "Picanha", False)
    marcar(pagina, "Picanha")           # volta cobrindo a falta
    assert alerta(pagina)[1] == cores().CERTO


# ---------------------------------------------------------------- marcadas em cima

def ordem(pagina):
    """Os textos da lista de carnes, na ordem da tela."""
    return textos(parte_que_rola(pagina))


def test_carne_marcada_sobe_para_o_seu_churrasco(app, pagina):
    marcar(pagina, "Coração de frango")
    tela = ordem(pagina)
    ultima_antes = app.plano.compras.carnes[-2].produto.nome
    coracao = tela.index("Coração de frango")
    assert tela.index(ultima_antes) < coracao < tela.index("Outras carnes")


def test_carne_desmarcada_desce_para_outras_carnes(pagina):
    marcar(pagina, "Linguiça toscana", False)
    tela = ordem(pagina)
    assert tela.index("Outras carnes") < tela.index("Linguiça toscana")


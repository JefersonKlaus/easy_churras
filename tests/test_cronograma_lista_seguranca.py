from datetime import datetime, timedelta

from churrasco_facil.catalogo_carnes import CORTES
from churrasco_facil.cronograma import (MINUTOS_PARA_BRASA, formatar_hora, gerar_cronograma,
                                        inicio_do_corte)
from churrasco_facil.lista_compras import (agrupar_por_secao, formatar_quantidade,
                                           linha_do_item, texto_da_lista)
from churrasco_facil.produtos import SECOES, ItemPlano, Produto
from churrasco_facil.seguranca import (AVISO_FRANGO, AVISO_LINGUICA, AVISO_PORCO, AVISOS_GERAIS,
                                       avisos_para)

SERVIR = datetime(2026, 11, 21, 14, 0)


def por_titulo(etapas):
    return {e.titulo: e for e in etapas}


# ---------------------------------------------------------------- cronograma

def test_etapas_da_picanha_de_tras_para_frente():
    etapas = gerar_cronograma(SERVIR, [CORTES["picanha"]])   # 25 min de grelha + 8 de descanso
    t = por_titulo(etapas)
    inicio = SERVIR - timedelta(minutes=33)
    assert t["Na grelha: Picanha"].hora == inicio
    assert t["Temperar: Picanha"].hora == inicio - timedelta(minutes=15)
    assert t["Tirar a carne da geladeira"].hora == inicio - timedelta(minutes=30)
    assert t["Acender o carvão"].hora == inicio - timedelta(minutes=MINUTOS_PARA_BRASA)
    assert t["Tirar e descansar: Picanha"].hora == SERVIR - timedelta(minutes=8)
    assert t["Servir!"].hora == SERVIR
    assert t["Comprar tudo"].hora == datetime(2026, 11, 20, 17, 0)
    assert t["Apagar e limpar"].hora == SERVIR + timedelta(hours=3)


def test_etapas_vem_em_ordem_de_hora():
    cortes = [CORTES[i] for i in ("picanha", "costelinha_suina", "linguica_toscana")]
    horas = [e.hora for e in gerar_cronograma(SERVIR, cortes)]
    assert horas == sorted(horas)


def test_carvao_acende_antes_do_corte_mais_demorado():
    cortes = [CORTES["picanha"], CORTES["costelinha_suina"]]   # costelinha: 120 + 8 min
    t = por_titulo(gerar_cronograma(SERVIR, cortes))
    assert t["Acender o carvão"].hora == inicio_do_corte(SERVIR, CORTES["costelinha_suina"]) \
        - timedelta(minutes=MINUTOS_PARA_BRASA)
    assert t["Na grelha: Costelinha suína"].hora < t["Na grelha: Picanha"].hora


def test_vegetariano_nao_tem_etapa_de_temperar_nem_descanso():
    t = por_titulo(gerar_cronograma(SERVIR, [CORTES["queijo_coalho"]]))
    assert "Temperar: Queijo coalho no espeto" not in t
    assert "Tirar e descansar: Queijo coalho no espeto" not in t
    assert "Na grelha: Queijo coalho no espeto" in t


def test_sem_cortes_ainda_tem_etapas_basicas():
    titulos = [e.titulo for e in gerar_cronograma(SERVIR, [])]
    assert "Servir!" in titulos and "Acender o carvão" not in titulos
    assert formatar_hora(SERVIR) == "14:00"


# ---------------------------------------------------------------- lista de compras

def item(unidade, quantidade, nome="X", secao="Mercearia", preco=100, por=1):
    return ItemPlano(Produto("x", nome, secao, unidade, preco, por), quantidade)


def test_formatar_quantidade():
    assert formatar_quantidade(item("g", 950)) == "950 g"
    assert formatar_quantidade(item("g", 1000)) == "1 kg"
    assert formatar_quantidade(item("g", 1200)) == "1,2 kg"
    assert formatar_quantidade(item("g", 1450)) == "1,45 kg"
    assert formatar_quantidade(item("ml", 1500)) == "1,5 L"
    assert formatar_quantidade(item("ml", 500)) == "500 ml"
    assert formatar_quantidade(item("un", 3)) == "3 un"


def test_agrupar_segue_a_ordem_do_mercado_e_ordena_por_nome():
    itens = [item("un", 1, "Zebra", "Bebidas"), item("g", 500, "Alcatra", "Açougue"),
             item("g", 500, "Bife", "Açougue"), item("un", 1, "Outro", "Seção nova")]
    grupos = agrupar_por_secao(itens)
    assert list(grupos) == ["Açougue", "Bebidas", "Seção nova"]
    assert [i.produto.nome for i in grupos["Açougue"]] == ["Alcatra", "Bife"]
    assert list(agrupar_por_secao([])) == []
    assert set(grupos) - {"Seção nova"} <= set(SECOES)


def test_texto_da_lista_com_e_sem_preco():
    produto = Produto("p", "Pão de alho", "Padaria", "un", 400, 1)
    itens = [ItemPlano(produto, 3, "para todos")]
    assert linha_do_item(itens[0]) == "Pão de alho: 3 un (para todos) - R$ 12,00"
    assert linha_do_item(itens[0], com_preco=False) == "Pão de alho: 3 un (para todos)"
    assert texto_da_lista(itens, com_preco=False) == "PADARIA\n- Pão de alho: 3 un (para todos)"


# ---------------------------------------------------------------- segurança

def test_avisos_gerais_sempre_aparecem_e_graves_vem_primeiro():
    avisos = avisos_para([CORTES["picanha"]])
    ids = [a.id for a in avisos]
    assert all(a.id in ids for a in AVISOS_GERAIS)
    assert AVISO_FRANGO.id not in ids and AVISO_PORCO.id not in ids
    primeiro_nao_grave = next(i for i, a in enumerate(avisos) if not a.grave)
    assert all(not a.grave for a in avisos[primeiro_nao_grave:])
    assert avisos[0].grave


def test_avisos_especificos_por_tipo_de_carne():
    ids = [a.id for a in avisos_para([CORTES["coxa_sobrecoxa"], CORTES["bisteca_suina"],
                                      CORTES["linguica_toscana"]])]
    assert AVISO_FRANGO.id in ids and AVISO_PORCO.id in ids and AVISO_LINGUICA.id in ids


def test_aviso_de_frango_e_grave_e_cita_a_temperatura():
    assert AVISO_FRANGO.grave and "74" in AVISO_FRANGO.texto
    monoxido = next(a for a in AVISOS_GERAIS if a.id == "monoxido")
    assert monoxido.grave and "fechado" in monoxido.titulo

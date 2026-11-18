# Churrasco Fácil

App em Python + Flet para quem nunca organizou um churrasco. Cada tela cuida de uma coisa só.

Visual Material 3, com uma cor de destaque (laranja brasa), cartões brancos, botões grandes
(56 px de altura, fáceis de tocar) e tudo centralizado. No celular, o app fica sempre em pé
(retrato). As configurações (engrenagem na tela inicial) só guardam a chave do Groq.

Para planejar, 4 passos. Em cima, ícones mostram em que passo você está (verde: feito; laranja:
agora; cinza: falta) e o X volta ao início. Embaixo, Voltar e Próximo ficam fixos:

1. **Preços**: todos os preços numa lista só, para conferir rápido (ficam salvos). O
   hortifruti (vinagrete e salada) tem uma chave: você decide se entra na conta. Mercearia
   (arroz, farinha, sal grosso) e descartáveis não têm preço: são só o "Não esqueça" da lista.
2. **Quem vem**: adultos, crianças, vegetarianos e quem bebe.
3. **Quando**: data, hora de servir e quanto tempo dura a festa.
4. **Escolha o churrasco**: Caprichado, Tradicional ou Simples, com o custo total e por pessoa.
   Toque no cartão da opção para escolher.

O plano escolhido abre com uma barra de abas no rodapé (a casinha no cabeçalho volta ao
início):

- **Carnes**: o que vai na grelha e quanto (toque numa carne para ver as dicas), o total e o
  botão Compartilhar.
- **Compras**: a lista de compras por seção do mercado e o "Não esqueça" (mercearia e
  descartáveis).
- **Horários**: **a que horas acender o carvão e colocar cada corte**, com os **cuidados de
  segurança de cada hora** (ex.: "nunca use álcool" na hora de acender; "frango a 74 °C" quando
  o frango vai para a grelha). Toque num horário para ver os detalhes.
- **Mestre**: a explicação do plano e as dúvidas.

Não há botão de salvar: ao abrir Compras ou Horários, o plano vai sozinho para "Meus churrascos".

A IA (Groq) só conversa (e é opcional): entende o pedido escrito livremente, explica o plano e
responde dúvidas. **Toda conta e toda regra de segurança é feita pelo
código**, e tudo que a IA devolve é validado. Sem chave ou sem internet o app funciona normalmente, usando o assistente local (veja *Modo offline*).

## Como rodar

```bash
pip install -e ".[dev]"      # ou: pip install "flet>=1.0" pytest
flet run                     # abre o app (usa src/main.py)
```

Testes (não precisam de rede nem de chave):

```bash
PYTHONPATH=src python3 -m pytest -q tests
```

Há um arquivo de teste para cada módulo (`tests/test_<modulo>.py`; o `modo_offline` é dividido
por assunto) e cada teste confere um comportamento só. Apoio compartilhado:
`conftest.py` (fixtures), `dados.py` (dados de exemplo) e `dubles.py` (Groq falso, sem rede).
As telas ficam em `tests/telas/`, sobre um Flet de mentira (`flet_falso.py`) e os ajudantes
de `tela.py` para achar textos e clicar.

## Chave do Groq (opcional)

- Variável de ambiente `GROQ_API_KEY` (tem prioridade), ou
- tela **Configurações** do app (salva em arquivo só do seu usuário, fora do projeto).

Nunca coloque a chave no código nem no GitHub. O arquivo `.env` está no `.gitignore`;
use `.env.exemplo` como modelo. O modelo usado é `llama-3.3-70b-versatile` (os nomes de
modelos mudam com o tempo; confira a documentação do Groq).

## Modo offline

Tudo funciona sem internet:

- **Cálculos, orçamento, horários, lista de compras, avisos e planos salvos**: sempre locais.
- **Contar o churrasco em texto** ("12 pessoas, 3 crianças, uns 400 reais"): o campo só aparece
  com a chave do Groq configurada; sem ela, use os contadores. Se o Groq falhar na hora, o
  `modo_offline` lê números, orçamento e duração sem IA. Se disser "12 pessoas e 3 crianças",
  conta as crianças dentro das 12 e pede para você conferir.
- **Opções de churrasco**: as carnes de cada opção e o custo são calculados pelo código.
- **Explicar o plano e tirar dúvidas** (ponto da carne, chuva, carvão acabando, fogo alto, frango,
  sobras...): textos prontos, mais respostas sobre o próprio plano (custo, horários, kg).
- Com a chave do Groq, a IA é usada primeiro; se a internet cair, o limite acabar ou a chave
  falhar, o app usa o modo offline sozinho e avisa na tela.
- O assistente offline não inventa resposta: se a dúvida não combina com nenhum assunto, diz
  isso e lista os assuntos que conhece.

### Instalar em um computador sem internet

1. Numa máquina **com** internet: `python offline/baixar_pacotes.py` (cria a pasta `vendor/`,
   que não vai para o GitHub).
2. Copie a pasta do projeto, com `vendor/`, para o outro computador. Os dois precisam ter o
   mesmo sistema e a mesma versão do Python.
3. No computador sem internet: `python offline/instalar_offline.py`, ative a `.venv` e rode
   `flet run`.

Os scripts do passo 1 e 3 ainda não foram testados com o Flet de verdade (não consegui
instalar o Flet no ambiente onde o código foi escrito). O `flet run` pode tentar baixar o
cliente do Flet na primeira vez; o script copia a pasta `~/.flet` quando ela existir.

## Onde ficam os dados

Pasta definida por `CHURRASCO_DADOS`; se não existir, `FLET_APP_STORAGE_DATA`; senão
`~/.churrasco_facil`. Lá ficam o banco de planos salvos e a configuração.

## Estrutura

- `calculadora`, `orcamento`, `cronograma`, `lista_compras`, `seguranca`: a lógica (sem IA).
- `catalogo_carnes`, `catalogo_itens`, `produtos`, `dinheiro`: catálogo e dinheiro em centavos.
- `opcoes`: as opções de churrasco (Caprichado, Tradicional, Simples) e o custo de cada uma.
- `linha_do_tempo`: junta horários e avisos de segurança (cada cuidado na hora em que importa).
- `cliente_groq`, `prompts`, `esquemas`, `assistente`, `conversa`: a camada de IA.
- `modo_offline`: assistente local (pedido, cortes, explicação, dúvidas) e reserva automática.
- `planejador`, `armazenamento`, `compartilhar`, `configuracao`, `entradas`: junta tudo.
- `app` e `telas/`: interface Flet. Cores e medidas ficam só em `telas/tema.py`; os
  componentes (botões, cartões, contador) em `telas/widgets.py`.

## Aviso

Os preços do catálogo são estimativas: confira e ajuste no primeiro passo do planejamento. As regras de segurança
(carvão só ao ar livre, frango bem passado, termômetro) valem como orientação geral.

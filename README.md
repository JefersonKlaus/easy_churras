# Churrasco Fácil

App em Python + Flet para quem nunca organizou um churrasco. Você diz quantas pessoas vêm, o
orçamento e a hora de servir; o app calcula **quanto comprar**, **quanto vai custar**, **a que
horas acender o carvão e colocar cada corte** e mostra os **avisos de segurança**.

A IA (Groq) só conversa (e é opcional): entende o pedido escrito livremente, sugere cortes do catálogo,
explica o plano e responde dúvidas. **Toda conta e toda regra de segurança é feita pelo
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

## Chave do Groq (opcional)

- Variável de ambiente `GROQ_API_KEY` (tem prioridade), ou
- tela **Configurações** do app (salva em arquivo só do seu usuário, fora do projeto).

Nunca coloque a chave no código nem no GitHub. O arquivo `.env` está no `.gitignore`;
use `.env.exemplo` como modelo. O modelo padrão é `llama-3.3-70b-versatile` e pode ser trocado
em Configurações (os nomes de modelos mudam com o tempo; confira a documentação do Groq).

## Modo offline

Tudo funciona sem internet:

- **Cálculos, orçamento, horários, lista de compras, avisos e planos salvos**: sempre locais.
- **Entender o texto** ("12 pessoas, 3 crianças, uns 400 reais"): o `modo_offline` lê números,
  orçamento e duração sem IA. Se disser "12 pessoas e 3 crianças", conta as crianças dentro
  das 12 e pede para você conferir.
- **Sugerir cortes**: regras por orçamento por pessoa, com crianças e tamanho do grupo.
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
- `cliente_groq`, `prompts`, `esquemas`, `assistente`, `conversa`: a camada de IA.
- `modo_offline`: assistente local (pedido, cortes, explicação, dúvidas) e reserva automática.
- `planejador`, `armazenamento`, `compartilhar`, `configuracao`, `entradas`: junta tudo.
- `app` e `telas/`: interface Flet.

## Aviso

Os preços do catálogo são estimativas editáveis em Configurações. As regras de segurança
(carvão só ao ar livre, frango bem passado, termômetro) valem como orientação geral.

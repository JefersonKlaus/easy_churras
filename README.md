# Churrasco Fácil

App em Python + Flet para quem nunca organizou um churrasco. Você diz quantas pessoas vêm, o
orçamento e a hora de servir; o app calcula **quanto comprar**, **quanto vai custar**, **a que
horas acender o carvão e colocar cada corte** e mostra os **avisos de segurança**.

A IA (Groq) só conversa: entende o pedido escrito livremente, sugere cortes do catálogo,
explica o plano e responde dúvidas. **Toda conta e toda regra de segurança é feita pelo
código**, e tudo que a IA devolve é validado. Sem chave do Groq o app funciona normalmente.

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

## Onde ficam os dados

Pasta definida por `CHURRASCO_DADOS`; se não existir, `FLET_APP_STORAGE_DATA`; senão
`~/.churrasco_facil`. Lá ficam o banco de planos salvos e a configuração.

## Estrutura

- `calculadora`, `orcamento`, `cronograma`, `lista_compras`, `seguranca`: a lógica (sem IA).
- `catalogo_carnes`, `catalogo_itens`, `produtos`, `dinheiro`: catálogo e dinheiro em centavos.
- `cliente_groq`, `prompts`, `esquemas`, `assistente`, `conversa`: a camada de IA.
- `planejador`, `armazenamento`, `compartilhar`, `configuracao`, `entradas`: junta tudo.
- `app` e `telas/`: interface Flet.

## Aviso

Os preços do catálogo são estimativas editáveis em Configurações. As regras de segurança
(carvão só ao ar livre, frango bem passado, termômetro) valem como orientação geral.

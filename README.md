# Churrasco Fácil

App em Python + Flet para quem nunca organizou um churrasco. Cada tela cuida de uma coisa só.

O foco é a grelha: carnes, bebidas (cerveja, refrigerante, água e gelo) e carvão. Toda bebida
segue a mesma regra, uma quantidade por pessoa que cresce com a duração da festa, e a lista
mostra quanto é indicado por pessoa (ex.: "Indicado: 1,7 L por pessoa que bebe"). Pão de alho,
farinha, sal grosso e descartáveis ficam fora da conta, no "Não esqueça". A carne é comprada como no
açougue, em **peças inteiras** (peça de picanha de ~1,2 kg, pacote de linguiça de 1 kg, bandeja
de frango de 1 kg, bife de contrafilé de 400 g...). O preço continua por kg.

Visual Material 3, com uma cor de destaque (laranja brasa, escuro o bastante para ler texto
pequeno), cartões brancos, botões grandes (56 px de altura, fáceis de tocar) e tudo
centralizado. No celular, o app fica sempre em pé
(retrato). As configurações (engrenagem na tela inicial) só guardam a chave do Groq.

Para planejar, 4 passos. Em cima, ícones mostram em que passo você está (verde: feito; laranja:
agora; cinza: falta) e o X volta ao início. Embaixo, Voltar e Próximo ficam fixos:

1. **Preços**: todos os preços numa lista só, para conferir rápido (ficam salvos). Pão de alho,
   mercearia (farinha, sal grosso) e descartáveis não têm preço: são só o "Não esqueça" da
   lista.
2. **Quem vem**: adultos, crianças, vegetarianos e quem bebe.
3. **Quando**: data, hora de servir e quanto tempo dura a festa.
4. **Escolha o churrasco**: Caprichado, Tradicional ou Simples, com quanto de carne e quais
   cortes cada um compra, e o custo total e por pessoa. Toque no cartão da opção para escolher.

O plano escolhido abre com 3 abas no rodapé e, logo acima delas, o botão **Salvar**, o mesmo em
todas as abas. Depois de salvo, ele vira **Início** (é por ele que se volta à tela inicial) e
volta a ser Salvar se algo mudar. Em cima ficam o nome do churrasco, quando é e para quantas
pessoas:

- **Carnes**: logo no começo, quanto custa (total e por pessoa) e quanto de carne. Depois, as
  carnes: **as melhores da opção escolhida já vêm marcadas** em "No seu churrasco", e as outras
  ficam embaixo, em "Outras carnes". Marcar uma carne a leva para cima (com uma peça, ou com as
  peças que cobrem o que está faltando); desmarcar a leva para baixo, sem mexer nas outras.
  No alto da tela, uma **faixa diz se a carne está certa** para o grupo: **vermelha** se falta,
  **verde** se está certa (um pouco a mais também é verde: com peças inteiras é normal) e
  **amarela** se é carne demais (mais de 25% acima do indicado). Tocar numa carne mostra **o que
  combina com ela e como escolher na hora de comprar** (como preparar fica nos Horários).
- **Compras**: a lista de compras por seção do mercado (cada bebida diz quanto é indicado por
  pessoa; **no cartão do açougue, cada carne diz como pedir ao açougueiro**, com uma dica geral
  no alto do cartão), o "Não esqueça" (pão de alho, farinha, sal grosso e descartáveis) e **quanto custa**:
  carnes, bebidas e carvão, parte por parte, e o total estimado (o "Não esqueça" fica fora). O botão
  **Compartilhar lista** abre o compartilhar do celular (WhatsApp...) com a lista; onde não
  houver, copia a lista.
- **Horários**: **lembretes simples, um por linha**. Na véspera: comprar, passar a carne do
  congelador para a geladeira e pôr a cerveja na geladeira. No dia: a farofa, acender o carvão,
  tirar a carne da geladeira, **começar pelo porco** (pelo menos 20 min antes das outras carnes;
  fica pronto antes e vira petisco). **Um cartão "Na grelha"** traz todas as carnes, cada uma
  com a sua hora, e **um cartão "Tirar e servir"** traz a hora de tirar cada uma (esperando o
  descanso do corte) e a hora de servir. Um triângulo marca a hora que pede um cuidado de
  segurança (vermelho se for grave, como "nunca use álcool" ao acender); tocar mostra o cuidado
  e **como preparar cada carne** (o ponto e as dicas de preparo).

O plano só vai para "Meus churrascos" pelo botão Salvar; salvar de novo grava por cima.
Excluir um churrasco salvo pede confirmação antes.

A IA (Groq) é opcional e, nesta versão, só entende o pedido escrito livremente no passo Quem
vem. **Toda conta e toda regra de segurança é feita pelo
código**, e tudo que a IA devolve é validado. Sem chave ou sem internet o app funciona normalmente, usando o assistente local (veja *Modo offline*).

## Como rodar

```bash
pip install -e ".[dev]"      # ou: pip install "flet>=1.0" pytest
flet run                     # abre o app (usa src/main.py)
```

Testes (não precisam de rede, de chave nem do Flet: as telas rodam sobre um Flet de mentira):

```bash
python -m pytest
```

Os testes espelham o código: **um arquivo de teste por módulo**, na pasta correspondente
(`src/churrasco_facil/telas/passos/precos.py` → `tests/telas/passos/test_precos.py`), e cada
teste confere um comportamento só. Apoio compartilhado: `tests/conftest.py` (fixtures) e, em
`tests/apoio/`, `dados.py` (dados de exemplo), `dubles.py` (Groq falso, sem rede),
`flet_falso.py` (o Flet de mentira) e `tela.py` (achar textos e tocar nas telas).

## Chave do Groq (opcional)

- Variável de ambiente `GROQ_API_KEY` (tem prioridade), ou
- tela **Configurações** do app (salva em arquivo só do seu usuário, fora do projeto).

Nunca coloque a chave no código nem no GitHub. O arquivo `.env` está no `.gitignore`;
use `.env.exemplo` como modelo. O modelo usado é `llama-3.3-70b-versatile` (os nomes de
modelos mudam com o tempo; confira a documentação do Groq).

## Modo offline

Tudo funciona sem internet:

- **Cálculos, horários, lista de compras, avisos e planos salvos**: sempre locais.
- **Contar o churrasco em texto** ("12 pessoas, 3 crianças, 1 vegetariano"): o campo só
  aparece com a chave do Groq configurada; sem ela, use os contadores. Se o Groq falhar na
  hora, o `modo_offline` lê os números e a duração sem IA. Se disser "12 pessoas e 3
  crianças", conta as crianças dentro das 12 e pede para você conferir.
- **Opções de churrasco**: as carnes de cada opção e o custo são calculados pelo código.
- Com a chave do Groq, a IA é usada primeiro; se a internet cair, o limite acabar ou a chave
  falhar, o app usa o modo offline sozinho e avisa na tela.

### Instalar em um computador sem internet

1. Numa máquina **com** internet: `python offline/baixar_pacotes.py` (cria a pasta `vendor/`,
   que não vai para o GitHub).
2. Copie a pasta do projeto, com `vendor/`, para o outro computador. Os dois precisam ter o
   mesmo sistema e a mesma versão do Python.
3. No computador sem internet: `python offline/instalar_offline.py`, ative a `.venv` e rode
   `flet run`.

Os scripts dos passos 1 e 3 ainda não foram testados. O `flet run` pode tentar baixar o
cliente do Flet na primeira vez; o script copia a pasta `~/.flet` quando ela existir.

## Onde ficam os dados

Pasta definida por `CHURRASCO_DADOS`; se não existir, `FLET_APP_STORAGE_DATA`; senão
`~/.churrasco_facil`. Lá ficam o banco de planos salvos e a configuração.

## Estrutura

Cada módulo cuida de uma coisa só.

- **Catálogo e dinheiro**: `produtos` (produto, item da compra e seções do mercado),
  `catalogo_carnes` (os cortes; `COMO_SE_COMPRA` diz como cada um é vendido e quanto pesa a
  peça; `COMBINA_COM` e `COMO_ESCOLHER` aparecem na aba Carnes, `COMO_PEDIR` e
  `DICA_DO_ACOUGUE` no açougue da aba Compras, e `ponto`/`preparo` nos Horários),
  `catalogo_itens` (bebidas, carvão e lembretes) e `dinheiro` (centavos, nunca float).
- **Quanto comprar**: `convidados` (quem vem), `parametros` (a tabela por pessoa), `pecas`
  (a carne em peças inteiras: `distribuir_em_pecas` segue a mistura da opção e pode ficar até
  5% abaixo do indicado; `ajustar_pecas` só mexe na carne marcada ou desmarcada),
  `calculadora` (cada item da compra) e `compras` (os itens e quanto custam).
- **O plano**: `opcoes` (Caprichado, Tradicional, Simples), `planejador` (do pedido ao plano,
  e se a carne está certa), `cronograma` (os horários), `seguranca` (os avisos, fixos no
  código) e `linha_do_tempo` (cada aviso na hora em que importa; os cartões dos Horários).
- **Mostrar e compartilhar**: `lista_compras` (quantidades por extenso e seções), `datas`
  (datas e horas na tela) e `compartilhar` (o texto da lista de compras).
- **O que a pessoa digita e guarda**: `entradas` (datas e horas digitadas), `rascunho` (o
  que ela contou nos passos), `precos` (os preços que ela confere), `configuracao` (o arquivo
  de configuração), `pastas` (onde ficam os dados), `serializacao` (o pedido em JSON) e
  `armazenamento` (Meus churrascos, em SQLite).
- **IA (opcional)**: `cliente_groq`, `prompts`, `esquemas` (valida o que a IA devolve) e
  `assistente`; `modo_offline/` lê o pedido sem IA (`texto`, `pedido`, `assistente_local`) e
  `reserva` usa o local quando o Groq falha.
- **Interface** (Flet): `app` (estado e navegação) e `telas/`: `tema` (cores e medidas, só
  aqui), `widgets` (botões, cartões, contador), `aparelho` (copiar, compartilhar, tela em pé),
  `navegacao` (abas e o botão Salvar/Início), `inicio`, `configuracoes`, `passos/` (o
  assistente, um módulo por passo) e as abas `carnes`, `compras` e `horarios`.

## Publicar nas lojas

O app é empacotado pelo Flet (`flet build`), que lê o `[tool.flet]` do `pyproject.toml`.

```bash
flet build aab        # Google Play (Android App Bundle)
flet build ipa        # App Store (num Mac com Xcode)
```

- **Identidade**: `bundle_id` (`com.easychurras.churrascofacil`) é a identidade do app nas
  lojas e **não pode mudar depois de publicar**: troque pelo domínio de quem publica antes
  do primeiro envio. Versão: `version` do `[project]` (a mesma de
  `churrasco_facil.__version__`).
- **Ícone e abertura**: `src/assets/icon.png` (o símbolo, para o Flet gerar todos os
  tamanhos com o fundo `icon_background`), `src/assets/icon_android.png` (o ícone pronto do
  Android) e `src/assets/splash.png`. Para refazer: `python ferramentas/gerar_icones.py`.
- **Para enviar à mão**: `docs/icones/app-store-1024.png` (ícone da App Store, sem
  transparência), `docs/icones/google-play-512.png` (ícone do Google Play) e
  `docs/icones/google-play-destaque-1024x500.png` (imagem de destaque do Google Play).
- **Capturas de tela**: `docs/screenshot/android/` (1080 x 1920, Google Play),
  `docs/screenshot/iphone-6.9/` (1290 x 2796) e `docs/screenshot/ipad-13/` (2048 x 2732, exigido
  porque o app também roda no iPad). São do app de verdade; para refazer, veja o começo de
  `ferramentas/capturar.mjs`.
- **Assinatura**: a chave do Android (`tool.flet.android.signing`) e o time/perfil da Apple
  (`tool.flet.ios`) ficam com quem publica; nunca vão para o repositório.

## Aviso

Os preços do catálogo são estimativas: confira e ajuste no primeiro passo do planejamento. As regras de segurança
(carvão só ao ar livre, frango bem passado, termômetro) valem como orientação geral.

# Plano de trabalho

Marque cada item quando terminar. Faça testes junto com cada módulo.

## Regras do projeto

1. Dinheiro sempre em centavos inteiros, nunca `float`.
2. O Groq só escolhe cortes por identificador do catálogo; o código recusa identificadores
   que não existem.
3. Resposta do Groq em JSON, sempre validada. Se vier inválida: tenta de novo uma vez e,
   se falhar, usa o plano calculado só pelo código.
4. Não enviar nomes nem contatos ao Groq: só contagens e preferências.
5. A chave fica em variável de ambiente, nunca no código.
6. Nomes de módulos, funções e variáveis em português, sem acento.

## Ordem de construção (versão enxuta)

- [x] `catalogo_carnes`: cortes, tempo de preparo, ponto, dificuldade, substitutos
- [x] `calculadora`: quantidades por perfil de convidado (tabela editável)
- [x] `orcamento`: custo e ajuste ao valor disponível
- [x] `cronograma`: horários calculados de trás para frente a partir da hora de servir
- [x] `lista_compras`: itens agrupados por seção do mercado
- [x] `seguranca`: regras fixas (monóxido de carbono, ponto da carne, contaminação)
- [x] `esquemas`: validação do JSON devolvido pelo Groq
- [x] `prompts`: instruções em português
- [x] `cliente_groq`: chamada à API, tempo limite, tentativas, erro 429
- [x] `planejador`: junta pedido, cálculo e plano
- [x] `armazenamento`: SQLite com os planos salvos
- [x] `compartilhar`: texto para colar no WhatsApp
- [x] `telas/`: assistente em passos, plano, lista, cronograma, conversa, configurações

## Testes

- Cliente falso do Groq com respostas gravadas à mão (sem rede e sem chave).
- Casos ruins: JSON quebrado, identificador inexistente, tempo esgotado, limite de uso.

## Estado atual

Tudo acima está escrito e testado (215 testes). Pendente: rodar as telas com o Flet de verdade
(`flet run`), porque os testes das telas usam um Flet de mentira e não conferem a aparência
nem detalhes da API (área de transferência, campos de texto).

# Churrasco Fácil

Aplicativo em Python + Flet que ajuda **quem nunca fez churrasco** a planejar o seu: quanto
comprar, quanto vai custar, o que fazer e a que horas, tudo em linguagem simples.

> Status: **em planejamento**. Este repositório ainda não tem código do aplicativo.

## Ideia central

- **O código faz as contas** (quantidades, custo, horários) e guarda as regras de segurança.
- **A IA do Groq conversa**: entende o pedido em texto livre, escolhe cortes de um catálogo,
  explica em palavras simples e responde dúvidas.
- O app continua útil **sem internet**: calculadora, lista e cronograma não dependem do Groq.

## Estrutura prevista

```
src/churrasco_facil/      código do aplicativo (nomes de módulos e funções em português)
src/churrasco_facil/telas/  telas do Flet
tests/                    testes
docs/                     decisões e anotações
```

## Segredos

A chave do Groq vem da variável de ambiente `GROQ_API_KEY` (veja `.env.exemplo`).
Nunca coloque chaves ou senhas no código nem no repositório.

## Plano de trabalho

Veja [docs/PLANO.md](docs/PLANO.md).

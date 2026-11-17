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

- [ ] `catalogo_carnes`: cortes, tempo de preparo, ponto, dificuldade, substitutos
- [ ] `calculadora`: quantidades por perfil de convidado (tabela editável)
- [ ] `orcamento`: custo e ajuste ao valor disponível
- [ ] `cronograma`: horários calculados de trás para frente a partir da hora de servir
- [ ] `lista_compras`: itens agrupados por seção do mercado
- [ ] `seguranca`: regras fixas (monóxido de carbono, ponto da carne, contaminação)
- [ ] `esquemas`: validação do JSON devolvido pelo Groq
- [ ] `prompts`: instruções em português
- [ ] `cliente_groq`: chamada à API, tempo limite, tentativas, erro 429
- [ ] `planejador`: junta pedido, cálculo e plano
- [ ] `armazenamento`: SQLite com os planos salvos
- [ ] `compartilhar`: texto para colar no WhatsApp
- [ ] `telas/`: assistente em passos, plano, lista, cronograma, conversa, configurações

## Testes

- Cliente falso do Groq com respostas gravadas à mão (sem rede e sem chave).
- Casos ruins: JSON quebrado, identificador inexistente, tempo esgotado, limite de uso.

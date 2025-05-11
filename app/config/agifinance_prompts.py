"""
Configurações e prompts específicos para o assistente do AgiFinance.
Este arquivo contém templates de prompts e configurações para adaptar
o assistente de IA ao contexto financeiro do AgiFinance.
"""

# Sistema de prompts para o AgiFinance
SYSTEM_PROMPT = """
Você é o assistente de IA do AgiFinance, uma plataforma moderna de gestão financeira pessoal.
Seu objetivo é ajudar os usuários a gerenciar suas finanças, entender conceitos financeiros e utilizar
efetivamente as funcionalidades do AgiFinance.

Principais recursos do AgiFinance que você deve conhecer:
- Autenticação de usuários com Clerk
- Gerenciamento de transações (adicionar, editar, excluir, categorizar)
- Dashboards e gráficos interativos
- Relatórios de gastos com IA
- Integração com assinaturas e pagamentos (Stripe)
- Interface responsiva com Tailwind CSS

Ao responder perguntas:
1. Seja conciso e direto
2. Forneça informações precisas sobre finanças pessoais
3. Explique como utilizar os recursos do AgiFinance quando relevante
4. Sugira boas práticas de gestão financeira
5. Mantenha um tom amigável e encorajador

Se você não souber a resposta ou se a pergunta estiver fora do escopo financeiro,
indique isso claramente e sugira onde o usuário pode encontrar a informação.
"""

# Prompt para gerar respostas com base em documentos recuperados
ANSWER_PROMPT = """
Contexto:
{context}

Histórico de conversa:
{chat_history}

Pergunta do usuário:
{question}

Responda à pergunta do usuário com base no contexto fornecido e no histórico da conversa.
Foque em informações relacionadas a finanças pessoais e ao uso da plataforma AgiFinance.
Se a resposta não estiver no contexto, responda com base em seu conhecimento sobre finanças pessoais,
mas indique claramente que está fornecendo informações gerais.
"""

# Dicas financeiras para incluir ocasionalmente nas respostas
FINANCIAL_TIPS = [
    "Mantenha um fundo de emergência equivalente a 3-6 meses de despesas.",
    "Acompanhe seus gastos diariamente para maior controle financeiro.",
    "Categorize suas despesas para identificar áreas onde pode economizar.",
    "Estabeleça metas financeiras claras e mensuráveis.",
    "Revise seu orçamento mensalmente e ajuste conforme necessário.",
    "Automatize suas economias configurando transferências automáticas.",
    "Priorize o pagamento de dívidas com juros altos.",
    "Invista regularmente, mesmo que sejam pequenas quantias.",
    "Diversifique seus investimentos para reduzir riscos.",
    "Planeje para a aposentadoria o quanto antes."
]

# Categorias financeiras padrão do AgiFinance
DEFAULT_CATEGORIES = [
    "Moradia", "Alimentação", "Transporte", "Saúde", "Educação", 
    "Lazer", "Vestuário", "Investimentos", "Dívidas", "Assinaturas",
    "Serviços", "Presentes", "Impostos", "Outros"
]

# Termos financeiros comuns para referência
FINANCIAL_GLOSSARY = {
    "juros compostos": "Juros que são calculados sobre o valor principal mais os juros acumulados anteriormente.",
    "inflação": "Aumento geral dos preços de bens e serviços em uma economia.",
    "diversificação": "Estratégia de distribuir investimentos entre diferentes ativos para reduzir riscos.",
    "liquidez": "Facilidade com que um ativo pode ser convertido em dinheiro sem perda significativa de valor.",
    "patrimônio líquido": "Valor total dos ativos menos o total de passivos de uma pessoa.",
    "fluxo de caixa": "Movimento de entrada e saída de dinheiro em um determinado período.",
    "orçamento": "Plano financeiro que aloca receitas para despesas, economias e investimentos.",
    "taxa de juros": "Percentual cobrado pelo uso do dinheiro emprestado ou pago pelo dinheiro investido.",
    "dívida de alto custo": "Dívidas com taxas de juros elevadas, como cartões de crédito.",
    "fundo de emergência": "Reserva financeira para cobrir despesas inesperadas ou períodos sem renda."
}

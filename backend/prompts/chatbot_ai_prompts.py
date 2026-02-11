"""
LK Clinic Tools - Chatbot AI Prompts
Claude API prompts for the intelligent FAQ chatbot node.
"""

SYSTEM_PROMPT = """Você é um assistente virtual de uma clínica de saúde no Brasil.

Regras:
1. Responda SEMPRE em português brasileiro (pt-BR)
2. Seja amigável, profissional e acolhedor
3. Use informações da base de conhecimento fornecida para responder
4. Se não souber a resposta, diga que vai encaminhar para um atendente
5. NUNCA dê diagnósticos médicos ou recomendações de tratamento
6. NUNCA invente informações - use apenas o que está na base de conhecimento
7. Mantenha respostas concisas (máximo 3 parágrafos)
8. Use emojis com moderação para um tom amigável
"""


def build_faq_prompt(
    question: str,
    knowledge_base: dict,
    conversation_history: list[dict] | None = None,
) -> str:
    """Build prompt for AI FAQ response using the clinic's knowledge base."""

    # Format knowledge base context
    kb_context = ""

    if knowledge_base.get("business_info"):
        info = knowledge_base["business_info"]
        kb_context += "INFORMAÇÕES DA CLÍNICA:\n"
        if info.get("hours"):
            kb_context += f"Horários: {info['hours']}\n"
        if info.get("location"):
            kb_context += f"Localização: {info['location']}\n"
        if info.get("parking"):
            kb_context += f"Estacionamento: {info['parking']}\n"
        if info.get("insurance"):
            kb_context += f"Convênios aceitos: {info['insurance']}\n"
        kb_context += "\n"

    if knowledge_base.get("services"):
        kb_context += "SERVIÇOS:\n"
        for svc in knowledge_base["services"]:
            kb_context += f"- {svc.get('name', '')}: {svc.get('description', '')}"
            if svc.get("duration"):
                kb_context += f" (Duração: {svc['duration']} min)"
            kb_context += "\n"
        kb_context += "\n"

    if knowledge_base.get("doctor_profiles"):
        kb_context += "PROFISSIONAIS:\n"
        for doc in knowledge_base["doctor_profiles"]:
            kb_context += f"- {doc.get('name', '')}: {doc.get('specialty', '')} - {doc.get('bio', '')}\n"
        kb_context += "\n"

    if knowledge_base.get("faqs"):
        kb_context += "PERGUNTAS FREQUENTES:\n"
        for faq in knowledge_base["faqs"]:
            kb_context += f"P: {faq.get('question', '')}\nR: {faq.get('answer', '')}\n\n"

    if knowledge_base.get("additional_context"):
        kb_context += f"INFORMAÇÕES ADICIONAIS:\n{knowledge_base['additional_context']}\n"

    # Format conversation history
    history = ""
    if conversation_history:
        history = "\nHISTÓRICO DA CONVERSA:\n"
        for msg in conversation_history[-5:]:  # Last 5 messages
            role = "Paciente" if msg.get("direction") == "inbound" else "Assistente"
            history += f"{role}: {msg.get('content', '')}\n"

    return f"""BASE DE CONHECIMENTO:
{kb_context}
{history}
PERGUNTA DO PACIENTE: {question}

Responda com base na base de conhecimento acima. Se a informação não estiver disponível, informe que vai encaminhar para um atendente humano."""

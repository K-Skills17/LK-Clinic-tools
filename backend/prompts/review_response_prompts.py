"""
LK Clinic Tools - Review Response Prompts
Claude API prompts for generating Google review responses.
"""

SYSTEM_PROMPT = """Você é um assistente que gera respostas para avaliações do Google de uma clínica de saúde no Brasil.

Regras OBRIGATÓRIAS:
1. Sempre responda em português brasileiro (pt-BR)
2. NUNCA mencione tratamentos, procedimentos ou diagnósticos específicos em respostas públicas
3. NUNCA seja defensivo ou argumentativo com avaliações negativas
4. Para reclamações, sempre convide para discussão offline (telefone ou presencial)
5. Use o nome do avaliador quando disponível
6. Mantenha as respostas concisas (2-4 frases)
7. Inclua o nome da clínica naturalmente
8. Demonstre empatia genuína, especialmente em avaliações negativas
"""


def build_review_response_prompt(
    clinic_name: str,
    reviewer_name: str,
    rating: int,
    review_text: str,
    tone: str,
    config: dict | None = None,
) -> str:
    """Build the prompt for generating a review response."""

    tone_instructions = {
        "profissional": "Tom formal e profissional. Agradeça de forma educada e objetiva.",
        "caloroso": "Tom caloroso e pessoal, típico brasileiro. Use palavras carinhosas e demonstre genuíno carinho pelo paciente.",
        "conciso": "Resposta curta e direta, máximo 2 frases. Agradeça e seja breve.",
    }

    tone_guide = tone_instructions.get(tone, tone_instructions["caloroso"])

    # Build context from config
    extra_context = ""
    if config:
        if config.get("doctor_names"):
            extra_context += f"\nMédicos da clínica: {', '.join(config['doctor_names'])}"
        if config.get("key_services"):
            extra_context += f"\nServiços principais: {', '.join(config['key_services'])}"
        if config.get("include_phrases"):
            extra_context += f"\nFrases a incluir quando possível: {', '.join(config['include_phrases'])}"
        if config.get("exclude_phrases"):
            extra_context += f"\nFrases a NUNCA usar: {', '.join(config['exclude_phrases'])}"

    # Few-shot examples from config
    examples = ""
    if config and config.get("example_responses"):
        examples = "\nExemplos de respostas aprovadas anteriormente:\n"
        for ex in config["example_responses"][:3]:
            examples += f"- \"{ex.get('text', '')}\"\n"

    sentiment = "positiva" if rating >= 4 else "neutra" if rating == 3 else "negativa"

    return f"""Gere uma resposta para esta avaliação do Google:

Clínica: {clinic_name}
Avaliador: {reviewer_name}
Estrelas: {rating}/5 ({sentiment})
Texto da avaliação: "{review_text}"

Tom desejado: {tone_guide}
{extra_context}
{examples}

Gere APENAS o texto da resposta, sem aspas ou formatação extra."""

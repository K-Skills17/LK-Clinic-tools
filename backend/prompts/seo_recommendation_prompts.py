"""
LK Clinic Tools - SEO Recommendation Prompts
Claude API prompts for generating actionable SEO recommendations.
"""

SYSTEM_PROMPT = """Você é um especialista em SEO local para clínicas de saúde no Brasil.
Gere recomendações práticas e acionáveis baseadas nos dados fornecidos.
Sempre responda em português brasileiro (pt-BR).
Priorize ações que terão maior impacto no ranking local do Google.
"""


def build_recommendation_prompt(
    clinic_name: str,
    gbp_data: dict,
    ranking_data: list[dict],
    competitor_data: list[dict],
    review_velocity: dict,
) -> str:
    """Build prompt for generating weekly SEO recommendations."""

    return f"""Analise os dados de SEO local da clínica e gere recomendações acionáveis.

CLÍNICA: {clinic_name}

PERFIL GOOGLE (GBP):
- Score de saúde: {gbp_data.get('health_score', 'N/A')}/100
- Score de completude: {gbp_data.get('completeness_score', 'N/A')}/100
- Total de avaliações: {gbp_data.get('review_count', 'N/A')}
- Média de avaliações: {gbp_data.get('average_rating', 'N/A')}
- Fotos: {gbp_data.get('photo_count', 'N/A')}
- Último post: {gbp_data.get('last_post_date', 'N/A')}
- Perguntas sem resposta: {gbp_data.get('qa_unanswered', 'N/A')}

RANKINGS:
{_format_rankings(ranking_data)}

CONCORRENTES:
{_format_competitors(competitor_data)}

VELOCIDADE DE AVALIAÇÕES:
- Este mês: {review_velocity.get('this_month', 'N/A')} novas avaliações
- Mês anterior: {review_velocity.get('last_month', 'N/A')} novas avaliações
- Tendência: {review_velocity.get('trend', 'N/A')}

Gere 3-5 recomendações ordenadas por prioridade (alta, média, baixa).
Para cada recomendação, inclua:
1. A ação específica a ser tomada
2. Por que é importante
3. Impacto esperado

Formato de saída (JSON):
[{{"recommendation": "texto", "priority": "alta|media|baixa", "reason": "por quê"}}]"""


def _format_rankings(rankings: list[dict]) -> str:
    if not rankings:
        return "Nenhum dado de ranking disponível."
    lines = []
    for r in rankings:
        pack = "✅ Local Pack" if r.get("in_local_pack") else "❌ Fora do Local Pack"
        lines.append(f"  - '{r.get('keyword', '')}': posição {r.get('rank_position', 'N/A')} ({pack})")
    return "\n".join(lines)


def _format_competitors(competitors: list[dict]) -> str:
    if not competitors:
        return "Nenhum dado de concorrentes disponível."
    lines = []
    for c in competitors:
        lines.append(
            f"  - {c.get('competitor_name', 'N/A')}: "
            f"{c.get('review_count', 0)} avaliações, "
            f"média {c.get('average_rating', 'N/A')}"
        )
    return "\n".join(lines)

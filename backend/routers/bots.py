"""
LK Clinic Tools - Bots Router
CRUD for chatbot management, deployment, and flow operations.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from dependencies import TenantContext, get_tenant_context, require_clinic_admin_or_above

router = APIRouter()


class BotCreate(BaseModel):
    name: str
    flow: dict
    channel: str = "whatsapp"
    widget_config: Optional[dict] = None


class BotUpdate(BaseModel):
    name: Optional[str] = None
    flow: Optional[dict] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    widget_config: Optional[dict] = None


@router.get("/")
async def list_bots(
    tenant: TenantContext = Depends(get_tenant_context),
):
    """List all chatbots for the clinic."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bots")
        .select("*")
        .eq("clinic_id", tenant.clinic_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {"bots": result.data or []}


@router.get("/templates")
async def get_bot_templates():
    """Get pre-built healthcare bot templates."""
    templates = [
        {
            "id": "agendamento",
            "name": "Agendamento",
            "description": "Bot para agendamento de consultas: saudação → seleção de serviço → data/hora → dados do paciente → confirmação",
            "flow": _get_agendamento_template(),
        },
        {
            "id": "faq_inteligente",
            "name": "FAQ Inteligente",
            "description": "Bot com IA para responder perguntas frequentes usando a base de conhecimento da clínica",
            "flow": _get_faq_template(),
        },
        {
            "id": "captacao_leads",
            "name": "Captação de Leads",
            "description": "Bot para capturar leads qualificados: interesse → contato → qualificação → encaminhar",
            "flow": _get_lead_capture_template(),
        },
        {
            "id": "pos_consulta",
            "name": "Pós-Consulta",
            "description": "Pesquisa de satisfação pós-consulta integrada com o módulo de avaliações",
            "flow": _get_post_appointment_template(),
        },
        {
            "id": "novo_paciente",
            "name": "Novo Paciente",
            "description": "Boas-vindas e orientações para novos pacientes: documentos, localização, preparação",
            "flow": _get_new_patient_template(),
        },
    ]

    return {"templates": templates}


@router.get("/{bot_id}")
async def get_bot(
    bot_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Get bot details including flow."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bots")
        .select("*")
        .eq("id", bot_id)
        .eq("clinic_id", tenant.clinic_id)
        .single()
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Bot não encontrado.")

    return result.data


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_bot(
    data: BotCreate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Create a new chatbot."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    bot_data = data.model_dump(exclude_none=True)
    bot_data["clinic_id"] = tenant.clinic_id

    result = db.table("bots").insert(bot_data).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar bot.")

    return result.data[0]


@router.patch("/{bot_id}")
async def update_bot(
    bot_id: str,
    data: BotUpdate,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Update bot configuration or flow."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    update_data = data.model_dump(exclude_none=True)

    result = (
        db.table("bots")
        .update(update_data)
        .eq("id", bot_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Bot não encontrado.")

    return result.data[0]


@router.post("/{bot_id}/deploy")
async def deploy_bot(
    bot_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Activate/deploy a bot."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bots")
        .update({"status": "active", "deployed_at": "now()"})
        .eq("id", bot_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Bot não encontrado.")

    return {"message": "Bot ativado com sucesso.", "bot": result.data[0]}


@router.post("/{bot_id}/pause")
async def pause_bot(
    bot_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Pause a deployed bot."""
    from services.supabase_client import get_supabase_admin

    db = get_supabase_admin()
    result = (
        db.table("bots")
        .update({"status": "paused"})
        .eq("id", bot_id)
        .eq("clinic_id", tenant.clinic_id)
        .execute()
    )

    if not result.data:
        raise HTTPException(status_code=404, detail="Bot não encontrado.")

    return {"message": "Bot pausado.", "bot": result.data[0]}


@router.get("/{bot_id}/widget-script")
async def get_widget_script(
    bot_id: str,
    tenant: TenantContext = Depends(get_tenant_context),
):
    """Generate embeddable widget script tag for a bot."""
    from config import get_settings

    settings = get_settings()

    script = f'<script src="{settings.app_base_url}/widget/chatbot.js" data-bot-id="{bot_id}" data-clinic-id="{tenant.clinic_id}" async></script>'

    return {"script_tag": script, "bot_id": bot_id}


# ============================================================
# Bot Flow Templates (simplified node structures)
# ============================================================

def _get_agendamento_template() -> dict:
    return {
        "nodes": [
            {"id": "start", "type": "mensagem", "data": {"text": "Olá! 😊 Bem-vindo(a) à {{clinica}}! Como posso ajudar?"}, "next": "menu"},
            {"id": "menu", "type": "mensagem", "data": {"text": "Escolha uma opção:", "buttons": [{"id": "agendar", "title": "Agendar consulta"}, {"id": "horarios", "title": "Ver horários"}, {"id": "falar", "title": "Falar com atendente"}]}, "next_map": {"agendar": "select_service", "horarios": "show_hours", "falar": "handoff"}},
            {"id": "select_service", "type": "input", "data": {"prompt": "Qual procedimento você deseja?", "variable": "servico", "input_type": "single_choice"}, "next": "select_date"},
            {"id": "select_date", "type": "input", "data": {"prompt": "Qual a melhor data para você? (ex: 15/03)", "variable": "data_preferida", "input_type": "text"}, "next": "collect_name"},
            {"id": "collect_name", "type": "input", "data": {"prompt": "Qual o seu nome completo?", "variable": "nome", "input_type": "text"}, "next": "collect_phone"},
            {"id": "collect_phone", "type": "input", "data": {"prompt": "Qual o seu telefone?", "variable": "telefone", "input_type": "text"}, "next": "confirm"},
            {"id": "confirm", "type": "mensagem", "data": {"text": "Perfeito! Vou confirmar:\n📋 {{servico}}\n📅 {{data_preferida}}\n👤 {{nome}}\n📱 {{telefone}}\n\nEstá correto?", "buttons": [{"id": "sim", "title": "✅ Sim"}, {"id": "nao", "title": "❌ Corrigir"}]}, "next_map": {"sim": "create_request", "nao": "select_service"}},
            {"id": "create_request", "type": "acao", "data": {"action": "create_appointment_request"}, "next": "done"},
            {"id": "done", "type": "mensagem", "data": {"text": "Pronto! Sua solicitação foi enviada. A equipe entrará em contato para confirmar. Obrigado! 😊"}},
            {"id": "show_hours", "type": "mensagem", "data": {"text": "Nossos horários:\n🕐 Seg-Sex: 8h às 18h\n🕐 Sáb: 8h às 12h"}, "next": "menu"},
            {"id": "handoff", "type": "transferencia", "data": {"message": "Vou te transferir para um atendente. Aguarde um momento..."}},
        ],
        "start_node": "start",
    }


def _get_faq_template() -> dict:
    return {
        "nodes": [
            {"id": "start", "type": "mensagem", "data": {"text": "Olá! Sou o assistente virtual da {{clinica}}. Como posso ajudar?"}, "next": "topic_menu"},
            {"id": "topic_menu", "type": "mensagem", "data": {"text": "Sobre o que gostaria de saber?", "buttons": [{"id": "servicos", "title": "Serviços"}, {"id": "planos", "title": "Planos/Convênios"}, {"id": "outro", "title": "Outra dúvida"}]}, "next_map": {"servicos": "ai_services", "planos": "ai_insurance", "outro": "ai_general"}},
            {"id": "ai_services", "type": "ai", "data": {"context": "services", "prompt": "Responda sobre os serviços da clínica"}, "next": "helpful_check"},
            {"id": "ai_insurance", "type": "ai", "data": {"context": "business_info", "prompt": "Responda sobre planos e convênios aceitos"}, "next": "helpful_check"},
            {"id": "ai_general", "type": "input", "data": {"prompt": "Digite sua pergunta:", "variable": "pergunta", "input_type": "text"}, "next": "ai_answer"},
            {"id": "ai_answer", "type": "ai", "data": {"context": "all", "prompt": "Responda a pergunta: {{pergunta}}"}, "next": "helpful_check"},
            {"id": "helpful_check", "type": "mensagem", "data": {"text": "Isso ajudou?", "buttons": [{"id": "sim", "title": "✅ Sim"}, {"id": "nao", "title": "❌ Não"}]}, "next_map": {"sim": "done", "nao": "handoff"}},
            {"id": "done", "type": "mensagem", "data": {"text": "Fico feliz em ajudar! Se precisar de mais alguma coisa, é só mandar mensagem. 😊"}, "next": "topic_menu"},
            {"id": "handoff", "type": "transferencia", "data": {"message": "Vou te conectar com um atendente para ajudar melhor. Aguarde..."}},
        ],
        "start_node": "start",
    }


def _get_lead_capture_template() -> dict:
    return {
        "nodes": [
            {"id": "start", "type": "mensagem", "data": {"text": "Olá! 😊 Que bom que você entrou em contato com a {{clinica}}!"}, "next": "interest"},
            {"id": "interest", "type": "input", "data": {"prompt": "Qual procedimento te interessa?", "variable": "interesse", "input_type": "text"}, "next": "collect_name"},
            {"id": "collect_name", "type": "input", "data": {"prompt": "Qual o seu nome?", "variable": "nome", "input_type": "text"}, "next": "collect_phone"},
            {"id": "collect_phone", "type": "input", "data": {"prompt": "Qual o melhor telefone para contato?", "variable": "telefone", "input_type": "text"}, "next": "qualify"},
            {"id": "qualify", "type": "mensagem", "data": {"text": "Você possui plano de saúde?", "buttons": [{"id": "sim", "title": "Sim"}, {"id": "nao", "title": "Não"}, {"id": "particular", "title": "Particular"}]}, "next_map": {"sim": "which_plan", "nao": "done_lead", "particular": "done_lead"}},
            {"id": "which_plan", "type": "input", "data": {"prompt": "Qual é o seu plano?", "variable": "plano", "input_type": "text"}, "next": "done_lead"},
            {"id": "done_lead", "type": "acao", "data": {"action": "tag_contact", "tag": "lead"}, "next": "thanks"},
            {"id": "thanks", "type": "mensagem", "data": {"text": "Obrigado, {{nome}}! Um de nossos consultores entrará em contato em breve para te ajudar. 😊"}},
        ],
        "start_node": "start",
    }


def _get_post_appointment_template() -> dict:
    return {
        "nodes": [
            {"id": "start", "type": "mensagem", "data": {"text": "Olá {{paciente}}! 😊 Obrigado pela visita à {{clinica}}!"}, "next": "satisfaction"},
            {"id": "satisfaction", "type": "mensagem", "data": {"text": "Como foi sua experiência?", "buttons": [{"id": "otima", "title": "😊 Ótima"}, {"id": "regular", "title": "😐 Regular"}, {"id": "ruim", "title": "😞 Ruim"}]}, "next_map": {"otima": "review_redirect", "regular": "feedback_collect", "ruim": "complaint_collect"}},
            {"id": "review_redirect", "type": "acao", "data": {"action": "trigger_review_request"}},
            {"id": "feedback_collect", "type": "input", "data": {"prompt": "O que podemos melhorar?", "variable": "feedback", "input_type": "text"}, "next": "feedback_thanks"},
            {"id": "feedback_thanks", "type": "mensagem", "data": {"text": "Agradecemos seu feedback! Vamos trabalhar para melhorar. 🙏"}},
            {"id": "complaint_collect", "type": "input", "data": {"prompt": "Lamentamos! Pode nos contar o que aconteceu?", "variable": "reclamacao", "input_type": "text"}, "next": "complaint_ack"},
            {"id": "complaint_ack", "type": "acao", "data": {"action": "create_negative_feedback"}},
        ],
        "start_node": "start",
    }


def _get_new_patient_template() -> dict:
    return {
        "nodes": [
            {"id": "start", "type": "mensagem", "data": {"text": "Bem-vindo(a) à {{clinica}}! 😊 Estamos felizes em recebê-lo(a)!"}, "next": "info_menu"},
            {"id": "info_menu", "type": "mensagem", "data": {"text": "Sobre o que gostaria de saber?", "buttons": [{"id": "docs", "title": "📄 Documentos"}, {"id": "local", "title": "📍 Localização"}, {"id": "prep", "title": "📋 Preparação"}]}, "next_map": {"docs": "documents", "local": "location", "prep": "preparation"}},
            {"id": "documents", "type": "mensagem", "data": {"text": "Para sua primeira consulta, traga:\n📄 RG e CPF\n💳 Cartão do plano de saúde\n📋 Exames anteriores (se houver)\n\nChegue 15 minutos antes para preencher sua ficha."}, "next": "more_info"},
            {"id": "location", "type": "mensagem", "data": {"text": "📍 {{endereco}}\n\n🚗 Estacionamento disponível\n🕐 Seg-Sex: 8h-18h | Sáb: 8h-12h"}, "next": "more_info"},
            {"id": "preparation", "type": "ai", "data": {"context": "services", "prompt": "Forneça orientações de preparação para primeira consulta"}, "next": "more_info"},
            {"id": "more_info", "type": "mensagem", "data": {"text": "Tem mais alguma dúvida?", "buttons": [{"id": "sim", "title": "Sim"}, {"id": "nao", "title": "Não, obrigado!"}]}, "next_map": {"sim": "info_menu", "nao": "done"}},
            {"id": "done", "type": "mensagem", "data": {"text": "Perfeito! Até logo! Se precisar, estamos aqui. 😊"}},
        ],
        "start_node": "start",
    }

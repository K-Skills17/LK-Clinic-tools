-- ============================================================
-- LK Clinic Tools - Database Schema & Seed Data
-- ============================================================
-- Run this against your Supabase PostgreSQL database
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Multi-tenant: Clinics
CREATE TABLE clinics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_name TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT NOT NULL,
    address TEXT,
    city TEXT,
    state TEXT,
    google_place_id TEXT,
    google_review_link TEXT,
    google_maps_url TEXT,
    -- WhatsApp config
    whatsapp_number TEXT,
    evolution_api_config JSONB,
    -- Branding
    logo_url TEXT,
    brand_colors JSONB DEFAULT '{}',
    -- Reminder config
    reminder_schedule JSONB DEFAULT '{"before_48h": true, "before_24h": true, "before_2h": true, "post_appointment": true, "noshow_followup": true}',
    reminder_sending_hours JSONB DEFAULT '{"start": "08:00", "end": "20:00"}',
    -- Review config
    review_request_delay_minutes INT DEFAULT 120,
    satisfaction_threshold INT DEFAULT 4,
    -- SEO config
    target_keywords TEXT[],
    competitor_place_ids TEXT[],
    -- Subscription
    plan TEXT DEFAULT 'standard' CHECK (plan IN ('basic', 'standard', 'premium')),
    subscription_status TEXT DEFAULT 'active' CHECK (subscription_status IN ('trial', 'active', 'paused', 'cancelled')),
    subscription_start DATE,
    subscription_price DECIMAL(10,2),
    -- Meta
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Clinic Users (multi-role)
CREATE TABLE clinic_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID,
    clinic_id UUID REFERENCES clinics(id),
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,
    role TEXT NOT NULL CHECK (role IN ('agency_admin', 'agency_operator', 'clinic_admin', 'clinic_staff')),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- MODULE 1: APPOINTMENTS
-- ============================================================

CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    patient_name TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INT DEFAULT 60,
    procedure_name TEXT,
    doctor_name TEXT,
    status TEXT DEFAULT 'pendente' CHECK (status IN ('pendente', 'confirmado', 'cancelado', 'remarcado', 'no_show', 'concluido')),
    confirmation_status TEXT DEFAULT 'nao_enviado' CHECK (confirmation_status IN ('nao_enviado', 'enviado', 'confirmado', 'recusado', 'sem_resposta')),
    source TEXT DEFAULT 'manual',
    notes TEXT,
    external_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE appointment_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
    reminder_type TEXT NOT NULL,
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'sent', 'responded', 'skipped', 'failed')),
    scheduled_for TIMESTAMPTZ NOT NULL,
    sent_at TIMESTAMPTZ,
    patient_response TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE procedures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    duration_default INT DEFAULT 60,
    pre_instructions TEXT,
    post_instructions TEXT,
    average_ticket DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE waitlist (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    patient_name TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    preferred_dates JSONB,
    preferred_procedures TEXT[],
    status TEXT DEFAULT 'waiting' CHECK (status IN ('waiting', 'notified', 'booked', 'expired')),
    notified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- MODULE 2: REVIEWS
-- ============================================================

CREATE TABLE review_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id),
    patient_name TEXT NOT NULL,
    patient_phone TEXT NOT NULL,
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'sent', 'satisfaction_received', 'review_link_sent', 'review_posted', 'no_response', 'negative_caught', 'neutral_caught')),
    satisfaction_score INT,
    feedback_text TEXT,
    review_link_clicked BOOLEAN DEFAULT false,
    google_review_detected BOOLEAN DEFAULT false,
    scheduled_for TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    responded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE google_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    google_review_id TEXT UNIQUE,
    reviewer_name TEXT,
    rating INT NOT NULL,
    text TEXT,
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative')),
    response_status TEXT DEFAULT 'pending' CHECK (response_status IN ('pending', 'drafted', 'approved', 'posted', 'skipped')),
    ai_response_options JSONB,
    selected_response TEXT,
    response_posted_at TIMESTAMPTZ,
    review_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE negative_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    review_request_id UUID REFERENCES review_requests(id),
    patient_name TEXT,
    patient_phone TEXT,
    complaint TEXT,
    assigned_to UUID REFERENCES clinic_users(id),
    resolution_status TEXT DEFAULT 'novo' CHECK (resolution_status IN ('novo', 'em_andamento', 'resolvido', 'sem_resolucao')),
    resolution_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE review_response_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    tone_preference TEXT DEFAULT 'caloroso',
    doctor_names TEXT[],
    key_services TEXT[],
    include_phrases TEXT[],
    exclude_phrases TEXT[],
    example_responses JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- MODULE 3: CHATBOT
-- ============================================================

CREATE TABLE bots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    flow JSONB NOT NULL,
    channel TEXT DEFAULT 'whatsapp' CHECK (channel IN ('whatsapp', 'website', 'both')),
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused')),
    widget_config JSONB,
    deployed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE knowledge_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    faqs JSONB DEFAULT '[]',
    services JSONB DEFAULT '[]',
    business_info JSONB DEFAULT '{}',
    doctor_profiles JSONB DEFAULT '[]',
    additional_context TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bot_contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    name TEXT,
    phone TEXT,
    email TEXT,
    captured_data JSONB DEFAULT '{}',
    tags TEXT[],
    source_bot_id UUID REFERENCES bots(id),
    source_channel TEXT,
    conversation_count INT DEFAULT 0,
    last_conversation_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE bot_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES bot_contacts(id),
    channel TEXT NOT NULL,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'bot', 'human', 'resolved')),
    assigned_to UUID REFERENCES clinic_users(id),
    current_node_id TEXT,
    variables JSONB DEFAULT '{}',
    started_at TIMESTAMPTZ DEFAULT now(),
    last_message_at TIMESTAMPTZ
);

CREATE TABLE bot_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES bot_conversations(id) ON DELETE CASCADE,
    direction TEXT NOT NULL CHECK (direction IN ('inbound', 'outbound')),
    sender_type TEXT NOT NULL CHECK (sender_type IN ('bot', 'human_agent', 'patient')),
    content TEXT,
    message_type TEXT DEFAULT 'text',
    node_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE appointment_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES bot_contacts(id),
    bot_conversation_id UUID REFERENCES bot_conversations(id),
    service TEXT,
    preferred_date TEXT,
    preferred_time TEXT,
    patient_name TEXT,
    patient_phone TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'cancelled')),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE canned_responses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- MODULE 4: SEO MONITOR
-- ============================================================

CREATE TABLE gbp_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    review_count INT,
    average_rating DECIMAL(2,1),
    photo_count INT,
    post_count INT,
    last_post_date DATE,
    qa_unanswered INT,
    completeness_score INT,
    health_score INT,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ranking_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    keyword TEXT NOT NULL,
    rank_position INT,
    in_local_pack BOOLEAN DEFAULT false,
    geo_point JSONB,
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE competitor_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    competitor_place_id TEXT NOT NULL,
    competitor_name TEXT,
    review_count INT,
    average_rating DECIMAL(2,1),
    snapshot_date DATE NOT NULL,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE seo_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    alert_type TEXT NOT NULL,
    severity TEXT DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'critical')),
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE seo_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    recommendation TEXT NOT NULL,
    priority TEXT DEFAULT 'media' CHECK (priority IN ('alta', 'media', 'baixa')),
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'implemented', 'dismissed')),
    ai_generated BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- SHARED: MESSAGE TEMPLATES
-- ============================================================

CREATE TABLE message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    module TEXT NOT NULL,
    step TEXT NOT NULL,
    message_text TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Contact deduplication
CREATE TABLE contact_dedup (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinics(id) ON DELETE CASCADE,
    patient_phone TEXT NOT NULL,
    last_review_request_at TIMESTAMPTZ,
    review_request_count INT DEFAULT 0,
    UNIQUE(clinic_id, patient_phone)
);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX idx_appointments_clinic_date ON appointments(clinic_id, appointment_date);
CREATE INDEX idx_appointments_status ON appointments(status);
CREATE INDEX idx_reminders_scheduled ON appointment_reminders(scheduled_for) WHERE status = 'scheduled';
CREATE INDEX idx_review_requests_clinic ON review_requests(clinic_id);
CREATE INDEX idx_review_requests_status ON review_requests(status);
CREATE INDEX idx_google_reviews_clinic ON google_reviews(clinic_id);
CREATE INDEX idx_bot_conversations_clinic ON bot_conversations(clinic_id, status);
CREATE INDEX idx_bot_messages_conversation ON bot_messages(conversation_id, created_at);
CREATE INDEX idx_gbp_snapshots_clinic ON gbp_snapshots(clinic_id, snapshot_date);
CREATE INDEX idx_ranking_snapshots_clinic ON ranking_snapshots(clinic_id, snapshot_date);
CREATE INDEX idx_seo_alerts_clinic ON seo_alerts(clinic_id, is_read);
CREATE INDEX idx_dedup_phone ON contact_dedup(clinic_id, patient_phone);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE clinics ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinic_users ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointment_reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE procedures ENABLE ROW LEVEL SECURITY;
ALTER TABLE waitlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE google_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE negative_feedback ENABLE ROW LEVEL SECURITY;
ALTER TABLE review_response_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE bots ENABLE ROW LEVEL SECURITY;
ALTER TABLE knowledge_bases ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointment_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE canned_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE gbp_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE ranking_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE competitor_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE seo_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE seo_recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE message_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE contact_dedup ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- REALTIME PUBLICATION
-- ============================================================

ALTER PUBLICATION supabase_realtime ADD TABLE bot_conversations, bot_messages, appointments, seo_alerts;

-- ============================================================
-- SEED DATA: Default Message Templates (pt-BR)
-- ============================================================
-- Note: These are inserted per-clinic during onboarding.
-- The following are template definitions used as defaults.

-- Function to create default templates for a new clinic
CREATE OR REPLACE FUNCTION create_default_templates(p_clinic_id UUID)
RETURNS void AS $$
BEGIN
    -- Reminder templates
    INSERT INTO message_templates (clinic_id, module, step, message_text) VALUES
    (p_clinic_id, 'reminder', 'before_48h',
     E'Olá {{paciente}}! 😊 Lembramos que você tem uma consulta agendada:\n📅 {{data}} às {{hora}}\n👨‍⚕️ {{doutor}}\n📍 {{clinica}} — {{endereco}}\n\nConfirma sua presença?\n✅ Confirmar\n❌ Preciso remarcar\n📋 Ver orientações pré-consulta'),
    (p_clinic_id, 'reminder', 'before_24h',
     E'{{paciente}}, sua consulta é amanhã às {{hora}}! Confirma?\n✅ Sim\n❌ Preciso remarcar'),
    (p_clinic_id, 'reminder', 'before_2h',
     E'{{paciente}}, sua consulta é daqui a 2 horas! 📍 {{endereco}}. Chegue 10 minutos antes. Até logo! 😊'),
    (p_clinic_id, 'reminder', 'noshow',
     E'{{paciente}}, notamos que não foi possível comparecer à consulta ontem. Gostaríamos de reagendar! Responda esta mensagem ou ligue: {{telefone_clinica}}');

    -- Review request templates
    INSERT INTO message_templates (clinic_id, module, step, message_text) VALUES
    (p_clinic_id, 'review', 'satisfaction_check',
     E'Olá {{paciente}}! 😊 Obrigado pela visita à {{clinica}} hoje!\n\nComo foi sua experiência?\n😊 Ótima\n😐 Regular\n😞 Ruim'),
    (p_clinic_id, 'review', 'positive_redirect',
     E'Ficamos muito felizes! 🎉 Sua opinião ajuda outras pessoas a nos conhecerem. Poderia deixar uma avaliação no Google? Leva menos de 1 minuto! 🙏\n\n{{google_review_link}}'),
    (p_clinic_id, 'review', 'positive_reminder',
     E'Ainda não conseguiu avaliar? Aqui está o link novamente: {{google_review_link}} 🙏'),
    (p_clinic_id, 'review', 'neutral_followup',
     E'Agradecemos seu feedback! O que podemos melhorar para tornar sua próxima visita ainda melhor?'),
    (p_clinic_id, 'review', 'negative_response',
     E'Lamentamos que sua experiência não tenha sido a melhor. Gostaríamos muito de entender o que aconteceu e resolver. Um responsável entrará em contato em breve.');
END;
$$ LANGUAGE plpgsql;

-- Function to create default procedures for a dental clinic
CREATE OR REPLACE FUNCTION create_default_dental_procedures(p_clinic_id UUID)
RETURNS void AS $$
BEGIN
    INSERT INTO procedures (clinic_id, name, duration_default, pre_instructions, post_instructions) VALUES
    (p_clinic_id, 'Limpeza dental', 60,
     'Chegue 10 minutos antes. Traga seu cartão do plano de saúde.',
     'Evite alimentos muito quentes ou frios nas próximas 2 horas.'),
    (p_clinic_id, 'Consulta inicial', 45,
     'Traga RG, CPF e cartão do plano. Chegue 15 minutos antes para preencher a ficha.',
     NULL),
    (p_clinic_id, 'Clareamento dental', 90,
     'Escove os dentes normalmente. Evite café e alimentos com corante no dia.',
     'Evite alimentos e bebidas com corante por 48 horas. Sensibilidade é normal.'),
    (p_clinic_id, 'Extração', 60,
     'Não fume nas 12 horas anteriores. Informe sobre medicamentos que esteja tomando.',
     'Aplique gelo na região por 15 minutos. Evite esforço físico por 48 horas. Tome a medicação prescrita.'),
    (p_clinic_id, 'Restauração', 45,
     'Chegue 10 minutos antes.',
     'A anestesia pode durar 2-3 horas. Evite morder o lábio ou bochecha.'),
    (p_clinic_id, 'Implante dentário', 120,
     'Jejum de 8 horas. Traga um acompanhante. Informe sobre medicamentos.',
     'Repouso absoluto por 48 horas. Aplique gelo. Dieta líquida/pastosa por 7 dias.');
END;
$$ LANGUAGE plpgsql;

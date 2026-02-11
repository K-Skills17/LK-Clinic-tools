/**
 * LK Clinic Tools - Utility Functions
 */

import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/** Merge Tailwind classes safely */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/** Format date to pt-BR format (DD/MM/YYYY) */
export function formatDate(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleDateString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

/** Format time to HH:MM */
export function formatTime(time: string): string {
  return time.slice(0, 5);
}

/** Format date + time */
export function formatDateTime(date: string | Date): string {
  const d = new Date(date);
  return d.toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

/** Format currency to BRL */
export function formatCurrency(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

/** Format phone number for display (+55 11 99999-9999) */
export function formatPhone(phone: string): string {
  const cleaned = phone.replace(/\D/g, "");
  if (cleaned.length === 13) {
    // +55 XX XXXXX-XXXX
    return `+${cleaned.slice(0, 2)} ${cleaned.slice(2, 4)} ${cleaned.slice(4, 9)}-${cleaned.slice(9)}`;
  }
  if (cleaned.length === 11) {
    // XX XXXXX-XXXX
    return `${cleaned.slice(0, 2)} ${cleaned.slice(2, 7)}-${cleaned.slice(7)}`;
  }
  return phone;
}

/** Get status badge color class */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    // Appointments
    pendente: "badge-warning",
    confirmado: "badge-success",
    cancelado: "badge-danger",
    remarcado: "badge-info",
    no_show: "badge-danger",
    concluido: "badge-success",
    // Confirmation
    nao_enviado: "badge-neutral",
    enviado: "badge-info",
    sem_resposta: "badge-warning",
    recusado: "badge-danger",
    // General
    active: "badge-success",
    paused: "badge-warning",
    draft: "badge-neutral",
    resolved: "badge-success",
    human: "badge-warning",
    // Review
    scheduled: "badge-neutral",
    sent: "badge-info",
    satisfaction_received: "badge-info",
    review_link_sent: "badge-success",
    review_posted: "badge-success",
    no_response: "badge-warning",
    negative_caught: "badge-danger",
    neutral_caught: "badge-warning",
    // Feedback
    novo: "badge-danger",
    em_andamento: "badge-warning",
    resolvido: "badge-success",
    sem_resolucao: "badge-neutral",
    // SEO
    info: "badge-info",
    warning: "badge-warning",
    critical: "badge-danger",
    // Subscription
    trial: "badge-info",
    cancelled: "badge-danger",
  };

  return colors[status] || "badge-neutral";
}

/** Translate status to pt-BR */
export function translateStatus(status: string): string {
  const translations: Record<string, string> = {
    pendente: "Pendente",
    confirmado: "Confirmado",
    cancelado: "Cancelado",
    remarcado: "Remarcado",
    no_show: "Não compareceu",
    concluido: "Concluído",
    nao_enviado: "Não enviado",
    enviado: "Enviado",
    sem_resposta: "Sem resposta",
    recusado: "Recusado",
    active: "Ativo",
    paused: "Pausado",
    draft: "Rascunho",
    resolved: "Resolvido",
    human: "Aguardando atendente",
    bot: "Bot ativo",
    scheduled: "Agendado",
    sent: "Enviado",
    satisfaction_received: "Satisfação recebida",
    review_link_sent: "Link enviado",
    review_posted: "Avaliação postada",
    no_response: "Sem resposta",
    negative_caught: "Negativo capturado",
    neutral_caught: "Neutro capturado",
    novo: "Novo",
    em_andamento: "Em andamento",
    resolvido: "Resolvido",
    sem_resolucao: "Sem resolução",
    pending: "Pendente",
    implemented: "Implementado",
    dismissed: "Descartado",
    trial: "Trial",
    cancelled: "Cancelado",
    waiting: "Aguardando",
    notified: "Notificado",
    booked: "Agendado",
    expired: "Expirado",
  };

  return translations[status] || status;
}

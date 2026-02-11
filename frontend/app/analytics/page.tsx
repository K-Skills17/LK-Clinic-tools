"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import {
  Calendar,
  Star,
  MessageSquare,
  Search,
  AlertTriangle,
  Users,
} from "lucide-react";

interface DashboardStats {
  appointments: {
    today_total: number;
    today_confirmed: number;
    this_week: number;
  };
  reviews: { pending_requests: number };
  chatbot: { active_conversations: number; needs_human: number };
  seo: {
    health_score: number | null;
    average_rating: number | null;
    review_count: number | null;
  };
  alerts: { unread: number };
}

export default function AnalyticsPage() {
  const { fetchClinicData } = useClinic();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<DashboardStats>("/analytics/dashboard")
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <Header title="Analytics" subtitle="Visao unificada de todos os modulos" />

      {loading ? (
        <LoadingSpinner />
      ) : stats ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Appointments */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <Calendar size={20} className="text-blue-600" />
              </div>
              <h3 className="font-semibold">Consultas</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Hoje</span>
                <span className="font-medium">{stats.appointments.today_total}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Confirmadas hoje</span>
                <span className="font-medium">{stats.appointments.today_confirmed}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Esta semana</span>
                <span className="font-medium">{stats.appointments.this_week}</span>
              </div>
            </div>
          </div>

          {/* Reviews */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center">
                <Star size={20} className="text-yellow-600" />
              </div>
              <h3 className="font-semibold">Avaliacoes</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Solicitacoes pendentes</span>
                <span className="font-medium">{stats.reviews.pending_requests}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Nota Google</span>
                <span className="font-medium">{stats.seo.average_rating || "-"}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Total Google</span>
                <span className="font-medium">{stats.seo.review_count || "-"}</span>
              </div>
            </div>
          </div>

          {/* Chatbot */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <MessageSquare size={20} className="text-green-600" />
              </div>
              <h3 className="font-semibold">Chatbot</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Conversas ativas</span>
                <span className="font-medium">{stats.chatbot.active_conversations}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Aguardando atendente</span>
                <span className="font-medium text-orange-600">{stats.chatbot.needs_human}</span>
              </div>
            </div>
          </div>

          {/* SEO */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <Search size={20} className="text-purple-600" />
              </div>
              <h3 className="font-semibold">SEO Local</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Saude GBP</span>
                <span className="font-medium">
                  {stats.seo.health_score != null ? `${stats.seo.health_score}/100` : "-"}
                </span>
              </div>
            </div>
          </div>

          {/* Alerts */}
          <div className="card">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                <AlertTriangle size={20} className="text-red-600" />
              </div>
              <h3 className="font-semibold">Alertas</h3>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Nao lidos</span>
              <span className="font-medium text-red-600">{stats.alerts.unread}</span>
            </div>
          </div>
        </div>
      ) : null}
    </DashboardLayout>
  );
}

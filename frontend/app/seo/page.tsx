"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import {
  Activity,
  Star,
  TrendingUp,
  Camera,
  MessageCircle,
  AlertTriangle,
} from "lucide-react";

interface SEODashboard {
  gbp_snapshot: {
    health_score: number;
    review_count: number;
    average_rating: number;
    photo_count: number;
    qa_unanswered: number;
    completeness_score: number;
  } | null;
  rankings: { keyword: string; rank_position: number; in_local_pack: boolean }[];
  alerts: { id: string; alert_type: string; severity: string; message: string }[];
  recommendations: { id: string; recommendation: string; priority: string }[];
}

export default function SEODashboardPage() {
  const { fetchClinicData } = useClinic();
  const [data, setData] = useState<SEODashboard | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<SEODashboard>("/seo/dashboard")
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <Header
        title="SEO Local"
        subtitle="Monitore sua presenca no Google e otimize seu perfil"
      />

      {loading ? (
        <LoadingSpinner />
      ) : !data?.gbp_snapshot ? (
        <div className="card text-center py-12">
          <Activity size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium mb-2">SEO nao configurado</h3>
          <p className="text-sm text-gray-500">
            Configure o Google Place ID nas configuracoes para ativar o monitoramento.
          </p>
        </div>
      ) : (
        <>
          {/* Health Score */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <div className="card col-span-1 flex flex-col items-center justify-center">
              <div className="text-4xl font-bold text-primary-600">
                {data.gbp_snapshot.health_score}
              </div>
              <p className="text-sm text-gray-500 mt-1">Saude GBP</p>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <Star size={16} className="text-yellow-500" />
                <span className="text-sm text-gray-500">Avaliacao</span>
              </div>
              <p className="text-2xl font-bold">{data.gbp_snapshot.average_rating}</p>
              <p className="text-xs text-gray-400">{data.gbp_snapshot.review_count} total</p>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <Camera size={16} className="text-blue-500" />
                <span className="text-sm text-gray-500">Fotos</span>
              </div>
              <p className="text-2xl font-bold">{data.gbp_snapshot.photo_count}</p>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <MessageCircle size={16} className="text-green-500" />
                <span className="text-sm text-gray-500">P&R sem resposta</span>
              </div>
              <p className="text-2xl font-bold">{data.gbp_snapshot.qa_unanswered}</p>
            </div>
            <div className="card">
              <div className="flex items-center gap-2 mb-1">
                <TrendingUp size={16} className="text-purple-500" />
                <span className="text-sm text-gray-500">Completude</span>
              </div>
              <p className="text-2xl font-bold">{data.gbp_snapshot.completeness_score}%</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Rankings */}
            <div className="card">
              <h3 className="font-semibold mb-4">Rankings</h3>
              {data.rankings.length === 0 ? (
                <p className="text-sm text-gray-500">Nenhum dado de ranking.</p>
              ) : (
                <div className="space-y-3">
                  {data.rankings.map((r, i) => (
                    <div key={i} className="flex items-center justify-between">
                      <span className="text-sm">{r.keyword}</span>
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold">
                          #{r.rank_position}
                        </span>
                        {r.in_local_pack && (
                          <span className="badge-success text-xs">Local Pack</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Alerts */}
            <div className="card">
              <h3 className="font-semibold mb-4">Alertas</h3>
              {data.alerts.length === 0 ? (
                <p className="text-sm text-gray-500">Nenhum alerta.</p>
              ) : (
                <div className="space-y-2">
                  {data.alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-start gap-2 p-2 rounded-lg bg-gray-50"
                    >
                      <AlertTriangle
                        size={16}
                        className={
                          alert.severity === "critical"
                            ? "text-red-500"
                            : alert.severity === "warning"
                            ? "text-yellow-500"
                            : "text-blue-500"
                        }
                      />
                      <span className="text-sm">{alert.message}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recommendations */}
          {data.recommendations.length > 0 && (
            <div className="card mt-6">
              <h3 className="font-semibold mb-4">Recomendacoes IA</h3>
              <div className="space-y-3">
                {data.recommendations.map((rec) => (
                  <div
                    key={rec.id}
                    className="flex items-start gap-3 p-3 border border-gray-200 rounded-lg"
                  >
                    <span
                      className={`badge text-xs ${
                        rec.priority === "alta"
                          ? "badge-danger"
                          : rec.priority === "media"
                          ? "badge-warning"
                          : "badge-info"
                      }`}
                    >
                      {rec.priority}
                    </span>
                    <p className="text-sm">{rec.recommendation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </DashboardLayout>
  );
}

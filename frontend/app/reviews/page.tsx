"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { formatDateTime } from "@/lib/utils";
import { Star, TrendingUp, ShieldCheck, ThumbsDown } from "lucide-react";

interface ReviewStats {
  total_requests: number;
  sent: number;
  responded: number;
  response_rate: number;
  positive: number;
  positive_rate: number;
  negative_caught: number;
  reviews_generated: number;
  conversion_rate: number;
}

interface ReviewRequest {
  id: string;
  patient_name: string;
  patient_phone: string;
  status: string;
  satisfaction_score: number | null;
  sent_at: string;
  responded_at: string;
}

export default function ReviewsPage() {
  const { fetchClinicData } = useClinic();
  const [stats, setStats] = useState<ReviewStats | null>(null);
  const [requests, setRequests] = useState<ReviewRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchClinicData<ReviewStats>("/review-requests/stats"),
      fetchClinicData<{ review_requests: ReviewRequest[] }>("/review-requests?limit=20"),
    ])
      .then(([statsData, requestsData]) => {
        setStats(statsData);
        setRequests(requestsData.review_requests);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { key: "patient_name", header: "Paciente" },
    {
      key: "status",
      header: "Status",
      render: (row: ReviewRequest) => <StatusBadge status={row.status} />,
    },
    {
      key: "satisfaction_score",
      header: "Satisfacao",
      render: (row: ReviewRequest) =>
        row.satisfaction_score ? (
          <div className="flex items-center gap-1">
            {Array.from({ length: 5 }, (_, i) => (
              <Star
                key={i}
                size={14}
                className={
                  i < row.satisfaction_score!
                    ? "text-yellow-400 fill-yellow-400"
                    : "text-gray-300"
                }
              />
            ))}
          </div>
        ) : (
          <span className="text-gray-400">-</span>
        ),
    },
    {
      key: "sent_at",
      header: "Enviado em",
      render: (row: ReviewRequest) =>
        row.sent_at ? formatDateTime(row.sent_at) : "-",
    },
  ];

  return (
    <DashboardLayout>
      <Header title="Avaliacoes" subtitle="Gerencie solicitacoes de avaliacoes e proteja sua reputacao" />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <>
          {/* Stats cards */}
          {stats && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                    <TrendingUp size={20} className="text-blue-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stats.response_rate}%</p>
                    <p className="text-xs text-gray-500">Taxa de resposta</p>
                  </div>
                </div>
              </div>
              <div className="card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                    <Star size={20} className="text-green-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stats.reviews_generated}</p>
                    <p className="text-xs text-gray-500">Avaliacoes geradas</p>
                  </div>
                </div>
              </div>
              <div className="card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-yellow-100 flex items-center justify-center">
                    <ShieldCheck size={20} className="text-yellow-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stats.positive_rate}%</p>
                    <p className="text-xs text-gray-500">Taxa positiva</p>
                  </div>
                </div>
              </div>
              <div className="card">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                    <ThumbsDown size={20} className="text-red-600" />
                  </div>
                  <div>
                    <p className="text-2xl font-bold">{stats.negative_caught}</p>
                    <p className="text-xs text-gray-500">Negativos capturados</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Review requests table */}
          <div className="card">
            <h3 className="font-semibold mb-4">Solicitacoes Recentes</h3>
            <DataTable
              columns={columns}
              data={requests}
              emptyMessage="Nenhuma solicitacao de avaliacao."
            />
          </div>
        </>
      )}
    </DashboardLayout>
  );
}

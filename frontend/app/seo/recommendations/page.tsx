"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { useClinic } from "@/hooks/useClinic";
import { Lightbulb, Check, X } from "lucide-react";
import toast from "react-hot-toast";

interface Recommendation {
  id: string;
  recommendation: string;
  priority: string;
  status: string;
  ai_generated: boolean;
}

export default function RecommendationsPage() {
  const { fetchClinicData, patchClinicData } = useClinic();
  const [recs, setRecs] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<{ recommendations: Recommendation[] }>("/seo/recommendations")
      .then((data) => setRecs(data.recommendations))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function updateStatus(id: string, status: string) {
    try {
      await patchClinicData(`/seo/recommendations/${id}?status=${status}`);
      setRecs((prev) => prev.filter((r) => r.id !== id));
      toast.success(status === "implemented" ? "Marcado como implementado!" : "Descartado.");
    } catch {
      toast.error("Erro ao atualizar.");
    }
  }

  return (
    <DashboardLayout>
      <Header
        title="Recomendacoes SEO"
        subtitle="Acoes sugeridas pela IA para melhorar seu posicionamento"
      />

      {loading ? (
        <LoadingSpinner />
      ) : recs.length === 0 ? (
        <EmptyState
          icon={<Lightbulb size={48} />}
          title="Nenhuma recomendacao pendente"
          description="Todas as recomendacoes foram implementadas ou descartadas."
        />
      ) : (
        <div className="space-y-3">
          {recs.map((rec) => (
            <div
              key={rec.id}
              className="card flex items-start gap-4"
            >
              <span
                className={`badge text-xs flex-shrink-0 ${
                  rec.priority === "alta"
                    ? "badge-danger"
                    : rec.priority === "media"
                    ? "badge-warning"
                    : "badge-info"
                }`}
              >
                {rec.priority}
              </span>
              <p className="text-sm flex-1">{rec.recommendation}</p>
              <div className="flex gap-2 flex-shrink-0">
                <button
                  onClick={() => updateStatus(rec.id, "implemented")}
                  className="p-2 rounded-lg hover:bg-green-50 text-green-600"
                  title="Implementado"
                >
                  <Check size={16} />
                </button>
                <button
                  onClick={() => updateStatus(rec.id, "dismissed")}
                  className="p-2 rounded-lg hover:bg-gray-100 text-gray-400"
                  title="Descartar"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

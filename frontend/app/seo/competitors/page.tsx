"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { Star } from "lucide-react";

interface CompetitorData {
  clinic: { review_count: number; average_rating: number } | null;
  competitors: {
    competitor_name: string;
    review_count: number;
    average_rating: number;
    snapshot_date: string;
  }[];
}

export default function CompetitorsPage() {
  const { fetchClinicData } = useClinic();
  const [data, setData] = useState<CompetitorData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<CompetitorData>("/seo/competitors")
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <Header
        title="Concorrentes"
        subtitle="Compare sua clinica com os concorrentes"
      />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="card">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-gray-500 text-xs">
                <th className="text-left py-3">Clinica</th>
                <th className="text-left py-3">Avaliacoes</th>
                <th className="text-left py-3">Media</th>
              </tr>
            </thead>
            <tbody>
              {/* Our clinic */}
              {data?.clinic && (
                <tr className="border-b bg-primary-50/50 font-medium">
                  <td className="py-3">Sua Clinica</td>
                  <td className="py-3">{data.clinic.review_count}</td>
                  <td className="py-3 flex items-center gap-1">
                    <Star size={14} className="text-yellow-400 fill-yellow-400" />
                    {data.clinic.average_rating}
                  </td>
                </tr>
              )}
              {/* Competitors */}
              {data?.competitors.map((comp, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-3">{comp.competitor_name}</td>
                  <td className="py-3">{comp.review_count}</td>
                  <td className="py-3 flex items-center gap-1">
                    <Star size={14} className="text-yellow-400 fill-yellow-400" />
                    {comp.average_rating}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {(!data?.competitors || data.competitors.length === 0) && (
            <p className="text-center text-gray-500 py-8 text-sm">
              Nenhum concorrente configurado. Adicione nas configuracoes.
            </p>
          )}
        </div>
      )}
    </DashboardLayout>
  );
}

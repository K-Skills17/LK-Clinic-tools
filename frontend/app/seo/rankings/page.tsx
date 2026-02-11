"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { formatDate } from "@/lib/utils";

interface RankingEntry {
  keyword: string;
  rank_position: number;
  in_local_pack: boolean;
  snapshot_date: string;
}

export default function RankingsPage() {
  const { fetchClinicData } = useClinic();
  const [rankings, setRankings] = useState<RankingEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<{ rankings: RankingEntry[] }>("/seo/rankings")
      .then((data) => setRankings(data.rankings))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  // Group by keyword
  const byKeyword: Record<string, RankingEntry[]> = {};
  for (const r of rankings) {
    if (!byKeyword[r.keyword]) byKeyword[r.keyword] = [];
    byKeyword[r.keyword].push(r);
  }

  return (
    <DashboardLayout>
      <Header
        title="Rankings"
        subtitle="Acompanhe sua posicao nas buscas locais do Google"
      />

      {loading ? (
        <LoadingSpinner />
      ) : Object.keys(byKeyword).length === 0 ? (
        <div className="card text-center py-8">
          <p className="text-gray-500">
            Nenhum dado de ranking. Configure palavras-chave nas configuracoes.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {Object.entries(byKeyword).map(([keyword, entries]) => (
            <div key={keyword} className="card">
              <h3 className="font-semibold mb-3">&ldquo;{keyword}&rdquo;</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-gray-500 text-xs">
                      <th className="text-left py-2">Data</th>
                      <th className="text-left py-2">Posicao</th>
                      <th className="text-left py-2">Local Pack</th>
                    </tr>
                  </thead>
                  <tbody>
                    {entries.map((entry, i) => (
                      <tr key={i} className="border-b border-gray-50">
                        <td className="py-2">{formatDate(entry.snapshot_date)}</td>
                        <td className="py-2 font-mono font-bold">
                          #{entry.rank_position}
                        </td>
                        <td className="py-2">
                          {entry.in_local_pack ? (
                            <span className="badge-success text-xs">Sim</span>
                          ) : (
                            <span className="badge-neutral text-xs">Nao</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { api } from "@/lib/api";
import { Building2, Star, MessageSquare, AlertTriangle } from "lucide-react";
import Link from "next/link";

interface ClinicSummary {
  id: string;
  business_name: string;
  city: string;
  state: string;
  plan: string;
  subscription_status: string;
  seo_health_score: number | null;
  average_rating: number | null;
  review_count: number | null;
  active_conversations: number;
  unread_alerts: number;
}

export default function AgencyOverviewPage() {
  const [data, setData] = useState<{ total_clinics: number; clinics: ClinicSummary[] } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api
      .get<{ total_clinics: number; clinics: ClinicSummary[] }>("/agency/overview")
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <Header
        title="Visao Geral da Agencia"
        subtitle={`${data?.total_clinics || 0} clinicas ativas`}
        actions={
          <Link href="/agency/clinics/new" className="btn-primary">
            + Nova Clinica
          </Link>
        }
      />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {data?.clinics.map((clinic) => (
            <Link
              key={clinic.id}
              href={`/agency/clinics/${clinic.id}`}
              className="card hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {clinic.business_name}
                  </h3>
                  <p className="text-sm text-gray-500">
                    {clinic.city}, {clinic.state}
                  </p>
                </div>
                <span className="badge-info text-xs">{clinic.plan}</span>
              </div>

              <div className="grid grid-cols-2 gap-3 mt-4">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Star size={14} className="text-yellow-500" />
                  <span>
                    {clinic.average_rating || "-"} ({clinic.review_count || 0})
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <MessageSquare size={14} className="text-blue-500" />
                  <span>{clinic.active_conversations} conversas</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Building2 size={14} className="text-green-500" />
                  <span>GBP: {clinic.seo_health_score || "-"}/100</span>
                </div>
                {clinic.unread_alerts > 0 && (
                  <div className="flex items-center gap-2 text-sm text-red-600">
                    <AlertTriangle size={14} />
                    <span>{clinic.unread_alerts} alertas</span>
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

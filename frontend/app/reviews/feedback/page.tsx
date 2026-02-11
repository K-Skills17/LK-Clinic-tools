"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { formatDateTime } from "@/lib/utils";

interface FeedbackTicket {
  id: string;
  patient_name: string;
  patient_phone: string;
  complaint: string;
  resolution_status: string;
  created_at: string;
  clinic_users: { name: string } | null;
}

export default function NegativeFeedbackPage() {
  const { fetchClinicData } = useClinic();
  const [feedback, setFeedback] = useState<FeedbackTicket[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<{ feedback: FeedbackTicket[] }>("/feedback")
      .then((data) => setFeedback(data.feedback))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { key: "patient_name", header: "Paciente" },
    {
      key: "complaint",
      header: "Reclamacao",
      render: (row: FeedbackTicket) => (
        <span className="text-sm text-gray-700 line-clamp-2">
          {row.complaint}
        </span>
      ),
    },
    {
      key: "resolution_status",
      header: "Status",
      render: (row: FeedbackTicket) => (
        <StatusBadge status={row.resolution_status} />
      ),
    },
    {
      key: "clinic_users",
      header: "Responsavel",
      render: (row: FeedbackTicket) =>
        row.clinic_users?.name || "Nao atribuido",
    },
    {
      key: "created_at",
      header: "Data",
      render: (row: FeedbackTicket) => formatDateTime(row.created_at),
    },
  ];

  return (
    <DashboardLayout>
      <Header
        title="Feedback Negativo"
        subtitle="Fila de resolucao de reclamacoes"
      />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="card">
          <DataTable
            columns={columns}
            data={feedback}
            emptyMessage="Nenhum feedback negativo pendente."
          />
        </div>
      )}
    </DashboardLayout>
  );
}

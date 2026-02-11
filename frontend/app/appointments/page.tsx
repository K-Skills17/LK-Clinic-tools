"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { formatDate, formatTime } from "@/lib/utils";
import { Plus, Upload, Calendar } from "lucide-react";
import Link from "next/link";

interface Appointment {
  id: string;
  patient_name: string;
  patient_phone: string;
  appointment_date: string;
  appointment_time: string;
  procedure_name: string;
  doctor_name: string;
  status: string;
  confirmation_status: string;
}

interface TodaySchedule {
  date: string;
  appointments: Appointment[];
  summary: {
    total: number;
    confirmed: number;
    pending: number;
    confirmation_rate: number;
  };
}

export default function AppointmentsPage() {
  const { fetchClinicData } = useClinic();
  const [schedule, setSchedule] = useState<TodaySchedule | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<TodaySchedule>("/appointments/today")
      .then(setSchedule)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    {
      key: "appointment_time",
      header: "Horario",
      render: (row: Appointment) => (
        <span className="font-mono font-medium">
          {formatTime(row.appointment_time)}
        </span>
      ),
    },
    { key: "patient_name", header: "Paciente" },
    { key: "procedure_name", header: "Procedimento" },
    { key: "doctor_name", header: "Doutor(a)" },
    {
      key: "status",
      header: "Status",
      render: (row: Appointment) => <StatusBadge status={row.status} />,
    },
    {
      key: "confirmation_status",
      header: "Confirmacao",
      render: (row: Appointment) => (
        <StatusBadge status={row.confirmation_status} />
      ),
    },
  ];

  return (
    <DashboardLayout>
      <Header
        title="Consultas de Hoje"
        subtitle={
          schedule
            ? `${schedule.summary.total} consultas | ${schedule.summary.confirmed} confirmadas (${schedule.summary.confirmation_rate}%)`
            : undefined
        }
        actions={
          <div className="flex gap-2">
            <Link href="/appointments/import" className="btn-secondary flex items-center gap-2">
              <Upload size={16} />
              Importar CSV
            </Link>
            <button className="btn-primary flex items-center gap-2">
              <Plus size={16} />
              Nova Consulta
            </button>
          </div>
        }
      />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="card">
          <DataTable
            columns={columns}
            data={schedule?.appointments || []}
            emptyMessage="Nenhuma consulta agendada para hoje."
          />
        </div>
      )}
    </DashboardLayout>
  );
}

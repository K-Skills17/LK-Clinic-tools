"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { formatDate } from "@/lib/utils";
import { Plus, Send, FileText } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

interface CampaignStats {
  total: number;
  pending: number;
  sent: number;
  failed: number;
  success_rate: number;
}

interface Campaign {
  id: string;
  name: string;
  status: string;
  created_at: string;
  stats: CampaignStats;
}

export default function CampaignsPage() {
  const { fetchClinicData, postClinicData } = useClinic();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  const loadCampaigns = () => {
    fetchClinicData<{ campaigns: Campaign[] }>("/campaigns")
      .then((res) => setCampaigns(res.campaigns))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadCampaigns();
  }, []);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    try {
      await postClinicData("/campaigns", { name: newName.trim() });
      setNewName("");
      setCreating(false);
      toast.success("Campanha criada!");
      loadCampaigns();
    } catch {
      toast.error("Erro ao criar campanha.");
    }
  };

  const columns = [
    {
      key: "name",
      header: "Nome",
      render: (row: Campaign) => (
        <Link
          href={`/campaigns/${row.id}`}
          className="text-primary-700 font-medium hover:underline"
        >
          {row.name}
        </Link>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row: Campaign) => <StatusBadge status={row.status} />,
    },
    {
      key: "stats",
      header: "Contatos",
      render: (row: Campaign) => (
        <span className="text-sm text-gray-600">
          {row.stats.total} total
        </span>
      ),
    },
    {
      key: "progress",
      header: "Progresso",
      render: (row: Campaign) => {
        if (row.stats.total === 0) return <span className="text-gray-400">-</span>;
        return (
          <div className="flex items-center gap-2">
            <div className="flex-1 bg-gray-200 rounded-full h-2 max-w-[120px]">
              <div
                className="bg-green-500 h-2 rounded-full"
                style={{
                  width: `${((row.stats.sent + row.stats.failed) / row.stats.total) * 100}%`,
                }}
              />
            </div>
            <span className="text-xs text-gray-500">
              {row.stats.sent}/{row.stats.total}
            </span>
          </div>
        );
      },
    },
    {
      key: "success_rate",
      header: "Taxa de Sucesso",
      render: (row: Campaign) => (
        <span className="text-sm">
          {row.stats.success_rate > 0 ? `${row.stats.success_rate}%` : "-"}
        </span>
      ),
    },
    {
      key: "created_at",
      header: "Criada em",
      render: (row: Campaign) => (
        <span className="text-sm text-gray-500">{formatDate(row.created_at)}</span>
      ),
    },
  ];

  return (
    <DashboardLayout>
      <Header
        title="Campanhas de Reativacao"
        subtitle="Envie mensagens em massa para reativar pacientes inativos"
        actions={
          <div className="flex gap-2">
            <Link
              href="/campaigns/drafts"
              className="btn-secondary flex items-center gap-2"
            >
              <FileText size={16} />
              Rascunhos
            </Link>
            <button
              onClick={() => setCreating(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Plus size={16} />
              Nova Campanha
            </button>
          </div>
        }
      />

      {creating && (
        <div className="card mb-4 p-4 flex items-center gap-3">
          <input
            type="text"
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Nome da campanha..."
            className="input flex-1"
            autoFocus
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          />
          <button onClick={handleCreate} className="btn-primary">
            Criar
          </button>
          <button
            onClick={() => {
              setCreating(false);
              setNewName("");
            }}
            className="btn-secondary"
          >
            Cancelar
          </button>
        </div>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="card">
          <DataTable
            columns={columns}
            data={campaigns}
            emptyMessage="Nenhuma campanha criada ainda."
          />
        </div>
      )}
    </DashboardLayout>
  );
}

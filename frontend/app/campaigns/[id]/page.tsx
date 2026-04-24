"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { formatDate } from "@/lib/utils";
import { Upload, Sparkles, Play, Pause, Users, Ban } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

interface Contact {
  id: string;
  name: string;
  phone: string;
  status: string;
  personalized_message: string | null;
  sent_at: string | null;
  error_message: string | null;
  created_at: string;
}

interface Campaign {
  id: string;
  name: string;
  status: string;
  created_at: string;
  stats: {
    total: number;
    pending: number;
    sent: number;
    failed: number;
    success_rate: number;
  };
}

interface AiUsage {
  count: number;
  limit: number;
  remaining: number;
}

export default function CampaignDetailPage() {
  const params = useParams();
  const campaignId = params.id as string;
  const { fetchClinicData, postClinicData, patchClinicData } = useClinic();

  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [aiUsage, setAiUsage] = useState<AiUsage | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [campaignData, contactsData, usageData] = await Promise.all([
        fetchClinicData<Campaign>(`/campaigns/${campaignId}`),
        fetchClinicData<{ contacts: Contact[] }>(`/campaigns/${campaignId}/contacts?limit=200`),
        fetchClinicData<AiUsage>("/ai-generate/usage"),
      ]);
      setCampaign(campaignData);
      setContacts(contactsData.contacts);
      setAiUsage(usageData);
    } catch {
      toast.error("Erro ao carregar campanha.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [campaignId]);

  const toggleStatus = async () => {
    if (!campaign) return;
    const newStatus = campaign.status === "active" ? "paused" : "active";
    try {
      await patchClinicData(`/campaigns/${campaignId}`, { status: newStatus });
      toast.success(newStatus === "active" ? "Campanha ativada!" : "Campanha pausada.");
      loadData();
    } catch {
      toast.error("Erro ao atualizar status.");
    }
  };

  const generateMessage = async (contact: Contact) => {
    setGenerating(contact.id);
    try {
      const result = await postClinicData<{ message: string; usage: AiUsage }>(
        "/ai-generate/generate",
        { patient_name: contact.name, tone: "amigavel" }
      );
      await patchClinicData(`/campaigns/${campaignId}/contacts/${contact.id}/message`, {
        contact_id: contact.id,
        message: result.message,
      });
      setAiUsage(result.usage);
      toast.success("Mensagem gerada!");
      loadData();
    } catch (err: any) {
      toast.error(err.message || "Erro ao gerar mensagem.");
    } finally {
      setGenerating(null);
    }
  };

  const columns = [
    { key: "name", header: "Nome" },
    {
      key: "phone",
      header: "Telefone",
      render: (row: Contact) => (
        <span className="font-mono text-sm">{row.phone}</span>
      ),
    },
    {
      key: "status",
      header: "Status",
      render: (row: Contact) => <StatusBadge status={row.status} />,
    },
    {
      key: "personalized_message",
      header: "Mensagem",
      render: (row: Contact) =>
        row.personalized_message ? (
          <span className="text-sm text-gray-600 truncate max-w-[200px] block">
            {row.personalized_message}
          </span>
        ) : (
          <button
            onClick={() => generateMessage(row)}
            disabled={generating === row.id || (aiUsage?.remaining ?? 0) <= 0}
            className="text-primary-600 hover:text-primary-800 text-sm flex items-center gap-1 disabled:opacity-50"
          >
            <Sparkles size={14} />
            {generating === row.id ? "Gerando..." : "Gerar IA"}
          </button>
        ),
    },
    {
      key: "sent_at",
      header: "Enviado",
      render: (row: Contact) =>
        row.sent_at ? (
          <span className="text-sm text-gray-500">{formatDate(row.sent_at)}</span>
        ) : row.error_message ? (
          <span className="text-sm text-red-500" title={row.error_message}>
            Erro
          </span>
        ) : (
          <span className="text-gray-400">-</span>
        ),
    },
  ];

  if (loading) {
    return (
      <DashboardLayout>
        <LoadingSpinner />
      </DashboardLayout>
    );
  }

  if (!campaign) {
    return (
      <DashboardLayout>
        <div className="text-center py-12 text-gray-500">
          Campanha nao encontrada.
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <Header
        title={campaign.name}
        subtitle={`${campaign.stats.total} contatos | ${campaign.stats.sent} enviados | ${campaign.stats.success_rate}% sucesso`}
        actions={
          <div className="flex gap-2">
            {aiUsage && (
              <span className="text-sm text-gray-500 self-center">
                IA: {aiUsage.remaining}/{aiUsage.limit} restantes
              </span>
            )}
            <Link
              href={`/campaigns/${campaignId}/import`}
              className="btn-secondary flex items-center gap-2"
            >
              <Upload size={16} />
              Importar CSV
            </Link>
            <button
              onClick={toggleStatus}
              className={`flex items-center gap-2 ${
                campaign.status === "active" ? "btn-secondary" : "btn-primary"
              }`}
            >
              {campaign.status === "active" ? (
                <>
                  <Pause size={16} /> Pausar
                </>
              ) : (
                <>
                  <Play size={16} /> Ativar
                </>
              )}
            </button>
          </div>
        }
      />

      {/* Stats cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-gray-900">{campaign.stats.total}</div>
          <div className="text-sm text-gray-500">Total</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-yellow-600">{campaign.stats.pending}</div>
          <div className="text-sm text-gray-500">Pendentes</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-green-600">{campaign.stats.sent}</div>
          <div className="text-sm text-gray-500">Enviados</div>
        </div>
        <div className="card p-4 text-center">
          <div className="text-2xl font-bold text-red-600">{campaign.stats.failed}</div>
          <div className="text-sm text-gray-500">Falhas</div>
        </div>
      </div>

      {/* Contacts table */}
      <div className="card">
        <DataTable
          columns={columns}
          data={contacts}
          emptyMessage="Nenhum contato importado. Use o botao Importar CSV."
        />
      </div>
    </DashboardLayout>
  );
}

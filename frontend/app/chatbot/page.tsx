"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { useClinic } from "@/hooks/useClinic";
import { Bot, Plus, MessageSquare, Users } from "lucide-react";
import Link from "next/link";

interface BotItem {
  id: string;
  name: string;
  channel: string;
  status: string;
  deployed_at: string | null;
  created_at: string;
}

export default function ChatbotListPage() {
  const { fetchClinicData } = useClinic();
  const [bots, setBots] = useState<BotItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<{ bots: BotItem[] }>("/bots")
      .then((data) => setBots(data.bots))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <DashboardLayout>
      <Header
        title="Chatbots"
        subtitle="Gerencie seus bots de atendimento"
        actions={
          <Link href="/chatbot/new" className="btn-primary flex items-center gap-2">
            <Plus size={16} />
            Novo Bot
          </Link>
        }
      />

      {loading ? (
        <LoadingSpinner />
      ) : bots.length === 0 ? (
        <EmptyState
          icon={<Bot size={48} />}
          title="Nenhum bot criado"
          description="Crie seu primeiro chatbot para automatizar o atendimento."
          action={
            <Link href="/chatbot/new" className="btn-primary">
              Criar Bot
            </Link>
          }
        />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {bots.map((bot) => (
            <Link
              key={bot.id}
              href={`/chatbot/${bot.id}`}
              className="card hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                    <Bot size={20} className="text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{bot.name}</h3>
                    <p className="text-xs text-gray-500">{bot.channel}</p>
                  </div>
                </div>
                <StatusBadge status={bot.status} />
              </div>
            </Link>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

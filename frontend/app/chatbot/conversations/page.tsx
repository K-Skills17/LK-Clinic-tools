"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { EmptyState } from "@/components/shared/EmptyState";
import { useClinic } from "@/hooks/useClinic";
import { MessageCircle, User } from "lucide-react";

interface Conversation {
  id: string;
  status: string;
  channel: string;
  last_message_at: string;
  bot_contacts: { name: string; phone: string } | null;
  bots: { name: string } | null;
}

export default function ConversationsPage() {
  const { fetchClinicData } = useClinic();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [filter, setFilter] = useState<string>("human");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConversations();
  }, [filter]);

  async function loadConversations() {
    setLoading(true);
    try {
      const endpoint =
        filter === "human"
          ? "/conversations/needs-human"
          : `/conversations?status_filter=${filter}`;
      const data = await fetchClinicData<{ conversations: Conversation[] }>(endpoint);
      setConversations(data.conversations);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <DashboardLayout>
      <Header title="Conversas" subtitle="Inbox de atendimento ao vivo" />

      {/* Filter tabs */}
      <div className="flex gap-2 mb-6">
        {[
          { key: "human", label: "Aguardando Atendente" },
          { key: "active", label: "Ativas" },
          { key: "resolved", label: "Resolvidas" },
        ].map((tab) => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === tab.key
                ? "bg-primary-100 text-primary-700"
                : "text-gray-500 hover:bg-gray-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : conversations.length === 0 ? (
        <EmptyState
          icon={<MessageCircle size={48} />}
          title="Nenhuma conversa"
          description={
            filter === "human"
              ? "Nenhuma conversa aguardando atendente."
              : "Nenhuma conversa neste filtro."
          }
        />
      ) : (
        <div className="space-y-2">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className="card flex items-center gap-4 cursor-pointer hover:shadow-md transition-shadow"
            >
              <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
                <User size={20} className="text-gray-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm truncate">
                  {conv.bot_contacts?.name || conv.bot_contacts?.phone || "Contato"}
                </p>
                <p className="text-xs text-gray-500">
                  via {conv.bots?.name || "Bot"} - {conv.channel}
                </p>
              </div>
              <StatusBadge status={conv.status} />
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

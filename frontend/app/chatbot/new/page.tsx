"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { api } from "@/lib/api";
import { Bot, Calendar, MessageSquare, UserPlus, Heart, Stethoscope } from "lucide-react";
import toast from "react-hot-toast";

interface BotTemplate {
  id: string;
  name: string;
  description: string;
  flow: object;
}

const templateIcons: Record<string, React.ReactNode> = {
  agendamento: <Calendar size={24} className="text-blue-600" />,
  faq_inteligente: <MessageSquare size={24} className="text-purple-600" />,
  captacao_leads: <UserPlus size={24} className="text-green-600" />,
  pos_consulta: <Heart size={24} className="text-red-600" />,
  novo_paciente: <Stethoscope size={24} className="text-teal-600" />,
};

export default function NewBotPage() {
  const { clinicId, postClinicData } = useClinic();
  const [templates, setTemplates] = useState<BotTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const router = useRouter();

  useEffect(() => {
    api
      .get<{ templates: BotTemplate[] }>(`/clinics/${clinicId}/bots/templates`)
      .then((data) => setTemplates(data.templates))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [clinicId]);

  async function createFromTemplate(template: BotTemplate) {
    setCreating(true);
    try {
      const bot = await postClinicData<{ id: string }>("/bots", {
        name: template.name,
        flow: template.flow,
        channel: "whatsapp",
      });
      toast.success("Bot criado com sucesso!");
      router.push(`/chatbot/${bot.id}`);
    } catch {
      toast.error("Erro ao criar bot.");
    } finally {
      setCreating(false);
    }
  }

  return (
    <DashboardLayout>
      <Header
        title="Novo Bot"
        subtitle="Escolha um template ou crie do zero"
      />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
          {templates.map((template) => (
            <button
              key={template.id}
              onClick={() => createFromTemplate(template)}
              disabled={creating}
              className="card text-left hover:shadow-md hover:border-primary-300 transition-all"
            >
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-lg bg-gray-50 flex items-center justify-center flex-shrink-0">
                  {templateIcons[template.id] || (
                    <Bot size={24} className="text-gray-600" />
                  )}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">
                    {template.name}
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {template.description}
                  </p>
                </div>
              </div>
            </button>
          ))}

          {/* Custom bot option */}
          <button
            onClick={() =>
              createFromTemplate({
                id: "custom",
                name: "Bot Personalizado",
                description: "",
                flow: { nodes: [], start_node: "start" },
              })
            }
            disabled={creating}
            className="card text-left hover:shadow-md hover:border-primary-300 transition-all border-dashed"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-lg bg-gray-50 flex items-center justify-center flex-shrink-0">
                <Bot size={24} className="text-gray-400" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">
                  Criar do Zero
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  Comece com um fluxo vazio e construa seu bot personalizado
                </p>
              </div>
            </div>
          </button>
        </div>
      )}
    </DashboardLayout>
  );
}

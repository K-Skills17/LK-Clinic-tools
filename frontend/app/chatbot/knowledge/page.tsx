"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { Plus, Trash2, Save } from "lucide-react";
import toast from "react-hot-toast";

interface KnowledgeBase {
  faqs: { question: string; answer: string }[];
  services: { name: string; description: string; duration: number; prep: string }[];
  business_info: Record<string, string>;
  doctor_profiles: { name: string; specialty: string; bio: string }[];
  additional_context: string;
}

export default function KnowledgeBasePage() {
  const { fetchClinicData, patchClinicData } = useClinic();
  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<"faqs" | "services" | "info" | "doctors">("faqs");

  useEffect(() => {
    fetchClinicData<KnowledgeBase>("/knowledge-base")
      .then(setKb)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function handleSave() {
    if (!kb) return;
    setSaving(true);
    try {
      await patchClinicData("/knowledge-base", kb);
      toast.success("Base de conhecimento salva!");
    } catch {
      toast.error("Erro ao salvar.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <DashboardLayout><LoadingSpinner /></DashboardLayout>;
  if (!kb) return null;

  const tabs = [
    { key: "faqs" as const, label: "FAQs" },
    { key: "services" as const, label: "Servicos" },
    { key: "info" as const, label: "Informacoes" },
    { key: "doctors" as const, label: "Profissionais" },
  ];

  return (
    <DashboardLayout>
      <Header
        title="Base de Conhecimento"
        subtitle="Informacoes usadas pelo chatbot com IA para responder pacientes"
        actions={
          <button
            onClick={handleSave}
            disabled={saving}
            className="btn-primary flex items-center gap-2"
          >
            <Save size={16} />
            {saving ? "Salvando..." : "Salvar"}
          </button>
        }
      />

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-primary-100 text-primary-700"
                : "text-gray-500 hover:bg-gray-100"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* FAQs */}
      {activeTab === "faqs" && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">Perguntas Frequentes</h3>
            <button
              onClick={() =>
                setKb({
                  ...kb,
                  faqs: [...kb.faqs, { question: "", answer: "" }],
                })
              }
              className="btn-secondary flex items-center gap-1 text-sm"
            >
              <Plus size={14} />
              Adicionar
            </button>
          </div>
          <div className="space-y-4">
            {kb.faqs.map((faq, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between mb-2">
                  <span className="text-xs text-gray-500">FAQ #{i + 1}</span>
                  <button
                    onClick={() =>
                      setKb({
                        ...kb,
                        faqs: kb.faqs.filter((_, idx) => idx !== i),
                      })
                    }
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                <input
                  placeholder="Pergunta"
                  value={faq.question}
                  onChange={(e) => {
                    const updated = [...kb.faqs];
                    updated[i] = { ...updated[i], question: e.target.value };
                    setKb({ ...kb, faqs: updated });
                  }}
                  className="input-field mb-2"
                />
                <textarea
                  placeholder="Resposta"
                  value={faq.answer}
                  onChange={(e) => {
                    const updated = [...kb.faqs];
                    updated[i] = { ...updated[i], answer: e.target.value };
                    setKb({ ...kb, faqs: updated });
                  }}
                  className="input-field"
                  rows={2}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Services */}
      {activeTab === "services" && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">Servicos</h3>
            <button
              onClick={() =>
                setKb({
                  ...kb,
                  services: [
                    ...kb.services,
                    { name: "", description: "", duration: 60, prep: "" },
                  ],
                })
              }
              className="btn-secondary flex items-center gap-1 text-sm"
            >
              <Plus size={14} />
              Adicionar
            </button>
          </div>
          <div className="space-y-4">
            {kb.services.map((svc, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between mb-2">
                  <span className="text-xs text-gray-500">
                    Servico #{i + 1}
                  </span>
                  <button
                    onClick={() =>
                      setKb({
                        ...kb,
                        services: kb.services.filter((_, idx) => idx !== i),
                      })
                    }
                    className="text-red-500 hover:text-red-700"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <input
                    placeholder="Nome do servico"
                    value={svc.name}
                    onChange={(e) => {
                      const updated = [...kb.services];
                      updated[i] = { ...updated[i], name: e.target.value };
                      setKb({ ...kb, services: updated });
                    }}
                    className="input-field"
                  />
                  <input
                    placeholder="Duracao (min)"
                    type="number"
                    value={svc.duration}
                    onChange={(e) => {
                      const updated = [...kb.services];
                      updated[i] = {
                        ...updated[i],
                        duration: parseInt(e.target.value) || 60,
                      };
                      setKb({ ...kb, services: updated });
                    }}
                    className="input-field"
                  />
                </div>
                <textarea
                  placeholder="Descricao"
                  value={svc.description}
                  onChange={(e) => {
                    const updated = [...kb.services];
                    updated[i] = { ...updated[i], description: e.target.value };
                    setKb({ ...kb, services: updated });
                  }}
                  className="input-field"
                  rows={2}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Business Info */}
      {activeTab === "info" && (
        <div className="card">
          <h3 className="font-semibold mb-4">Informacoes da Clinica</h3>
          <div className="space-y-4">
            {["hours", "location", "parking", "insurance"].map((field) => (
              <div key={field}>
                <label className="label capitalize">{field}</label>
                <input
                  value={kb.business_info[field] || ""}
                  onChange={(e) =>
                    setKb({
                      ...kb,
                      business_info: {
                        ...kb.business_info,
                        [field]: e.target.value,
                      },
                    })
                  }
                  className="input-field"
                  placeholder={`Informe ${field}`}
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Doctors */}
      {activeTab === "doctors" && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="font-semibold">Profissionais</h3>
            <button
              onClick={() =>
                setKb({
                  ...kb,
                  doctor_profiles: [
                    ...kb.doctor_profiles,
                    { name: "", specialty: "", bio: "" },
                  ],
                })
              }
              className="btn-secondary flex items-center gap-1 text-sm"
            >
              <Plus size={14} />
              Adicionar
            </button>
          </div>
          <div className="space-y-4">
            {kb.doctor_profiles.map((doc, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-4">
                <div className="grid grid-cols-2 gap-2 mb-2">
                  <input
                    placeholder="Nome"
                    value={doc.name}
                    onChange={(e) => {
                      const updated = [...kb.doctor_profiles];
                      updated[i] = { ...updated[i], name: e.target.value };
                      setKb({ ...kb, doctor_profiles: updated });
                    }}
                    className="input-field"
                  />
                  <input
                    placeholder="Especialidade"
                    value={doc.specialty}
                    onChange={(e) => {
                      const updated = [...kb.doctor_profiles];
                      updated[i] = { ...updated[i], specialty: e.target.value };
                      setKb({ ...kb, doctor_profiles: updated });
                    }}
                    className="input-field"
                  />
                </div>
                <textarea
                  placeholder="Bio"
                  value={doc.bio}
                  onChange={(e) => {
                    const updated = [...kb.doctor_profiles];
                    updated[i] = { ...updated[i], bio: e.target.value };
                    setKb({ ...kb, doctor_profiles: updated });
                  }}
                  className="input-field"
                  rows={2}
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </DashboardLayout>
  );
}

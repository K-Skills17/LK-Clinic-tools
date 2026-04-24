"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { Plus, Pencil, Trash2, ArrowLeft, Copy } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

interface Draft {
  id: string;
  name: string;
  template_text: string;
  created_at: string;
}

export default function DraftsPage() {
  const { fetchClinicData, postClinicData, patchClinicData, deleteClinicData } =
    useClinic();
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ name: "", template_text: "" });

  const loadDrafts = () => {
    fetchClinicData<{ drafts: Draft[] }>("/campaigns/drafts")
      .then((res) => setDrafts(res.drafts))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadDrafts();
  }, []);

  const handleSave = async () => {
    if (!form.name.trim() || !form.template_text.trim()) {
      toast.error("Preencha todos os campos.");
      return;
    }

    try {
      if (editing) {
        await patchClinicData(`/campaigns/drafts/${editing}`, form);
        toast.success("Rascunho atualizado!");
      } else {
        await postClinicData("/campaigns/drafts", form);
        toast.success("Rascunho criado!");
      }
      setForm({ name: "", template_text: "" });
      setEditing(null);
      setCreating(false);
      loadDrafts();
    } catch {
      toast.error("Erro ao salvar.");
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Excluir este rascunho?")) return;
    try {
      await deleteClinicData(`/campaigns/drafts/${id}`);
      toast.success("Rascunho excluido.");
      loadDrafts();
    } catch {
      toast.error("Erro ao excluir.");
    }
  };

  const handleEdit = (draft: Draft) => {
    setEditing(draft.id);
    setCreating(true);
    setForm({ name: draft.name, template_text: draft.template_text });
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success("Copiado!");
  };

  return (
    <DashboardLayout>
      <Header
        title="Rascunhos de Mensagem"
        subtitle="Templates reutilizaveis para campanhas de reativacao"
        actions={
          <div className="flex gap-2">
            <Link
              href="/campaigns"
              className="btn-secondary flex items-center gap-2"
            >
              <ArrowLeft size={16} />
              Campanhas
            </Link>
            <button
              onClick={() => {
                setCreating(true);
                setEditing(null);
                setForm({ name: "", template_text: "" });
              }}
              className="btn-primary flex items-center gap-2"
            >
              <Plus size={16} />
              Novo Rascunho
            </button>
          </div>
        }
      />

      {/* Create/Edit form */}
      {creating && (
        <div className="card p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">
            {editing ? "Editar Rascunho" : "Novo Rascunho"}
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome
              </label>
              <input
                type="text"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                placeholder="Ex: Reativacao limpeza"
                className="input w-full"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Mensagem
              </label>
              <textarea
                value={form.template_text}
                onChange={(e) =>
                  setForm({ ...form, template_text: e.target.value })
                }
                placeholder="Ola {{paciente}}, faz tempo que nao nos vemos..."
                rows={4}
                className="input w-full"
              />
              <p className="text-xs text-gray-400 mt-1">
                Use {"{{paciente}}"} para o nome do paciente
              </p>
            </div>
            <div className="flex gap-2">
              <button onClick={handleSave} className="btn-primary">
                Salvar
              </button>
              <button
                onClick={() => {
                  setCreating(false);
                  setEditing(null);
                }}
                className="btn-secondary"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Drafts list */}
      {loading ? (
        <LoadingSpinner />
      ) : drafts.length === 0 ? (
        <div className="card p-12 text-center text-gray-500">
          Nenhum rascunho salvo.
        </div>
      ) : (
        <div className="space-y-3">
          {drafts.map((draft) => (
            <div key={draft.id} className="card p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{draft.name}</h4>
                  <p className="text-sm text-gray-600 mt-1 whitespace-pre-wrap">
                    {draft.template_text}
                  </p>
                </div>
                <div className="flex gap-1 ml-4">
                  <button
                    onClick={() => copyToClipboard(draft.template_text)}
                    className="p-2 text-gray-400 hover:text-gray-600"
                    title="Copiar"
                  >
                    <Copy size={16} />
                  </button>
                  <button
                    onClick={() => handleEdit(draft)}
                    className="p-2 text-gray-400 hover:text-primary-600"
                    title="Editar"
                  >
                    <Pencil size={16} />
                  </button>
                  <button
                    onClick={() => handleDelete(draft.id)}
                    className="p-2 text-gray-400 hover:text-red-600"
                    title="Excluir"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
}

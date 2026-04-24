"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { useClinic } from "@/hooks/useClinic";
import { Upload, ArrowLeft, FileSpreadsheet } from "lucide-react";
import Link from "next/link";
import toast from "react-hot-toast";

interface ImportResult {
  imported: number;
  skipped: number;
  errors: Array<{ row: number; phone?: string; error: string }>;
}

export default function ImportContactsPage() {
  const params = useParams();
  const router = useRouter();
  const campaignId = params.id as string;
  const { clinicId } = useClinic();
  const { postClinicData } = useClinic();

  const [file, setFile] = useState<File | null>(null);
  const [manualInput, setManualInput] = useState("");
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);

  const handleFileImport = async () => {
    if (!file) return;
    setImporting(true);
    try {
      const text = await file.text();
      const lines = text.trim().split("\n");
      const header = lines[0].toLowerCase();
      const delimiter = header.includes(";") ? ";" : ",";

      const contacts: Array<{ name: string; phone: string }> = [];
      for (let i = 1; i < lines.length; i++) {
        const cols = lines[i].split(delimiter).map((c) => c.trim().replace(/"/g, ""));
        if (cols.length >= 2) {
          contacts.push({ name: cols[0], phone: cols[1] });
        } else if (cols.length === 1) {
          contacts.push({ name: "", phone: cols[0] });
        }
      }

      const res = await postClinicData<ImportResult>(
        `/campaigns/${campaignId}/contacts`,
        { contacts }
      );
      setResult(res);
      toast.success(`${res.imported} contatos importados!`);
    } catch {
      toast.error("Erro ao importar arquivo.");
    } finally {
      setImporting(false);
    }
  };

  const handleManualImport = async () => {
    if (!manualInput.trim()) return;
    setImporting(true);
    try {
      const lines = manualInput
        .trim()
        .split("\n")
        .filter((l) => l.trim());

      const contacts = lines.map((line) => {
        const parts = line.split(/[;,\t]/).map((p) => p.trim());
        if (parts.length >= 2) {
          return { name: parts[0], phone: parts[1] };
        }
        return { name: "", phone: parts[0] };
      });

      const res = await postClinicData<ImportResult>(
        `/campaigns/${campaignId}/contacts`,
        { contacts }
      );
      setResult(res);
      toast.success(`${res.imported} contatos importados!`);
    } catch {
      toast.error("Erro ao importar contatos.");
    } finally {
      setImporting(false);
    }
  };

  return (
    <DashboardLayout>
      <Header
        title="Importar Contatos"
        subtitle="Adicione contatos a esta campanha via CSV ou manualmente"
        actions={
          <Link
            href={`/campaigns/${campaignId}`}
            className="btn-secondary flex items-center gap-2"
          >
            <ArrowLeft size={16} />
            Voltar
          </Link>
        }
      />

      <div className="grid grid-cols-2 gap-6">
        {/* CSV Upload */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileSpreadsheet size={20} />
            Importar CSV
          </h3>
          <p className="text-sm text-gray-500 mb-4">
            Arquivo CSV com colunas: nome;telefone (separado por ponto-e-virgula)
          </p>
          <input
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 mb-4"
          />
          <button
            onClick={handleFileImport}
            disabled={!file || importing}
            className="btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-50"
          >
            <Upload size={16} />
            {importing ? "Importando..." : "Importar Arquivo"}
          </button>
        </div>

        {/* Manual input */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold mb-4">Adicionar Manualmente</h3>
          <p className="text-sm text-gray-500 mb-4">
            Um contato por linha: nome;telefone
          </p>
          <textarea
            value={manualInput}
            onChange={(e) => setManualInput(e.target.value)}
            placeholder={"Maria Silva;11987654321\nJoao Santos;11976543210"}
            rows={8}
            className="input w-full mb-4 font-mono text-sm"
          />
          <button
            onClick={handleManualImport}
            disabled={!manualInput.trim() || importing}
            className="btn-primary w-full disabled:opacity-50"
          >
            {importing ? "Importando..." : "Importar Contatos"}
          </button>
        </div>
      </div>

      {/* Results */}
      {result && (
        <div className="card p-6 mt-6">
          <h3 className="text-lg font-semibold mb-3">Resultado</h3>
          <div className="flex gap-6 mb-4">
            <div>
              <span className="text-green-600 font-bold text-xl">{result.imported}</span>
              <span className="text-sm text-gray-500 ml-1">importados</span>
            </div>
            <div>
              <span className="text-yellow-600 font-bold text-xl">{result.skipped}</span>
              <span className="text-sm text-gray-500 ml-1">ignorados (duplicados/bloqueados)</span>
            </div>
            <div>
              <span className="text-red-600 font-bold text-xl">{result.errors.length}</span>
              <span className="text-sm text-gray-500 ml-1">erros</span>
            </div>
          </div>
          {result.errors.length > 0 && (
            <div className="bg-red-50 rounded p-3">
              <p className="text-sm font-medium text-red-800 mb-2">Erros:</p>
              {result.errors.slice(0, 10).map((err, i) => (
                <p key={i} className="text-xs text-red-600">
                  Linha {err.row}: {err.error}
                  {err.phone && ` (${err.phone})`}
                </p>
              ))}
              {result.errors.length > 10 && (
                <p className="text-xs text-red-500 mt-1">
                  ...e mais {result.errors.length - 10} erros
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </DashboardLayout>
  );
}

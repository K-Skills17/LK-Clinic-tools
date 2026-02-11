"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { useClinic } from "@/hooks/useClinic";
import { api } from "@/lib/api";
import { Upload, FileSpreadsheet, CheckCircle, AlertCircle } from "lucide-react";
import toast from "react-hot-toast";

export default function ImportAppointmentsPage() {
  const { clinicId } = useClinic();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<{
    imported: number;
    errors: { row: number; error: string }[];
  } | null>(null);

  async function handleUpload() {
    if (!file || !clinicId) return;

    setUploading(true);
    try {
      const res = await api.upload<{
        imported: number;
        errors: { row: number; error: string }[];
        message: string;
      }>(`/clinics/${clinicId}/appointments/import`, file);

      setResult({ imported: res.imported, errors: res.errors });
      toast.success(res.message);
    } catch (error: any) {
      toast.error(error.message || "Erro ao importar.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <DashboardLayout>
      <Header
        title="Importar Consultas"
        subtitle="Importe consultas a partir de um arquivo CSV"
      />

      <div className="max-w-2xl">
        <div className="card">
          <h3 className="font-semibold mb-4">Formato do CSV</h3>
          <p className="text-sm text-gray-600 mb-3">
            O arquivo CSV deve usar ponto e virgula (;) como separador e conter
            as seguintes colunas:
          </p>
          <div className="bg-gray-50 rounded-lg p-4 font-mono text-xs text-gray-700 mb-6">
            patient_name;patient_phone;appointment_date;appointment_time;procedure_name;doctor_name;duration_minutes;notes
            <br />
            Maria Silva;5519999998888;2025-03-15;09:00;Limpeza dental;Dr. Carlos;60;Primeira consulta
          </div>

          {/* Upload area */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <FileSpreadsheet size={40} className="mx-auto text-gray-400 mb-3" />
            <p className="text-sm text-gray-600 mb-3">
              Arraste um arquivo CSV ou clique para selecionar
            </p>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              className="hidden"
              id="csv-upload"
            />
            <label htmlFor="csv-upload" className="btn-secondary cursor-pointer">
              Selecionar arquivo
            </label>
            {file && (
              <p className="mt-3 text-sm text-gray-700">{file.name}</p>
            )}
          </div>

          {file && (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className="btn-primary w-full mt-4 flex items-center justify-center gap-2"
            >
              <Upload size={16} />
              {uploading ? "Importando..." : "Importar"}
            </button>
          )}
        </div>

        {/* Results */}
        {result && (
          <div className="card mt-6">
            <div className="flex items-center gap-2 text-green-600 mb-3">
              <CheckCircle size={20} />
              <span className="font-semibold">
                {result.imported} consultas importadas
              </span>
            </div>

            {result.errors.length > 0 && (
              <>
                <div className="flex items-center gap-2 text-red-600 mb-2">
                  <AlertCircle size={20} />
                  <span className="font-semibold">
                    {result.errors.length} erros
                  </span>
                </div>
                <ul className="text-sm text-gray-600 space-y-1">
                  {result.errors.map((err, i) => (
                    <li key={i}>
                      Linha {err.row}: {err.error}
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}

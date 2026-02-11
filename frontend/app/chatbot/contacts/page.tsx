"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import { DataTable } from "@/components/shared/DataTable";
import { LoadingSpinner } from "@/components/shared/LoadingSpinner";
import { useClinic } from "@/hooks/useClinic";
import { formatPhone, formatDateTime } from "@/lib/utils";
import { Download } from "lucide-react";

interface Contact {
  id: string;
  name: string;
  phone: string;
  email: string;
  tags: string[];
  source_channel: string;
  conversation_count: number;
  created_at: string;
}

export default function ContactsPage() {
  const { fetchClinicData, clinicId } = useClinic();
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchClinicData<{ contacts: Contact[] }>("/contacts")
      .then((data) => setContacts(data.contacts))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const columns = [
    { key: "name", header: "Nome" },
    {
      key: "phone",
      header: "Telefone",
      render: (row: Contact) => formatPhone(row.phone || ""),
    },
    { key: "email", header: "Email" },
    {
      key: "tags",
      header: "Tags",
      render: (row: Contact) => (
        <div className="flex gap-1 flex-wrap">
          {(row.tags || []).map((tag) => (
            <span key={tag} className="badge-info text-xs">
              {tag}
            </span>
          ))}
        </div>
      ),
    },
    { key: "conversation_count", header: "Conversas" },
    {
      key: "created_at",
      header: "Capturado em",
      render: (row: Contact) => formatDateTime(row.created_at),
    },
  ];

  return (
    <DashboardLayout>
      <Header
        title="Contatos"
        subtitle="Contatos capturados pelos chatbots"
        actions={
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL}/api/clinics/${clinicId}/contacts/export`}
            className="btn-secondary flex items-center gap-2"
          >
            <Download size={16} />
            Exportar CSV
          </a>
        }
      />

      {loading ? (
        <LoadingSpinner />
      ) : (
        <div className="card">
          <DataTable
            columns={columns}
            data={contacts}
            emptyMessage="Nenhum contato capturado."
          />
        </div>
      )}
    </DashboardLayout>
  );
}

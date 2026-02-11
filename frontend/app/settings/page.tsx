"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { Header } from "@/components/layout/Header";
import Link from "next/link";
import {
  Bell,
  Star,
  FileText,
  Users,
  Settings,
} from "lucide-react";

const settingsLinks = [
  {
    href: "/settings/reminders",
    label: "Lembretes",
    description: "Configure horarios e regras de envio de lembretes",
    icon: <Bell size={24} className="text-blue-600" />,
  },
  {
    href: "/settings/reviews",
    label: "Avaliacoes",
    description: "Configure o fluxo de solicitacao de avaliacoes",
    icon: <Star size={24} className="text-yellow-600" />,
  },
  {
    href: "/settings/templates",
    label: "Templates de Mensagem",
    description: "Personalize as mensagens enviadas aos pacientes",
    icon: <FileText size={24} className="text-green-600" />,
  },
  {
    href: "/settings/team",
    label: "Equipe",
    description: "Gerencie usuarios e permissoes da clinica",
    icon: <Users size={24} className="text-purple-600" />,
  },
];

export default function SettingsPage() {
  return (
    <DashboardLayout>
      <Header title="Configuracoes" />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-3xl">
        {settingsLinks.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className="card hover:shadow-md transition-shadow flex items-start gap-4"
          >
            <div className="w-12 h-12 rounded-lg bg-gray-50 flex items-center justify-center flex-shrink-0">
              {link.icon}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{link.label}</h3>
              <p className="text-sm text-gray-500 mt-1">{link.description}</p>
            </div>
          </Link>
        ))}
      </div>
    </DashboardLayout>
  );
}

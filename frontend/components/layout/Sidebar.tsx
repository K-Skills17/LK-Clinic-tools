"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Calendar,
  Star,
  MessageSquare,
  Search,
  BarChart3,
  Settings,
  Building2,
  LayoutDashboard,
  Users,
  ClipboardList,
  MessageCircle,
  Bot,
  Globe,
  AlertTriangle,
  Lightbulb,
  FileText,
  LogOut,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/hooks/useAuth";

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  roles?: string[];
  children?: NavItem[];
}

const navigation: NavItem[] = [
  // Agency routes
  {
    label: "Visão Geral",
    href: "/agency",
    icon: <Building2 size={20} />,
    roles: ["agency_admin", "agency_operator"],
  },
  // Clinic routes
  {
    label: "Consultas",
    href: "/appointments",
    icon: <Calendar size={20} />,
  },
  {
    label: "Avaliações",
    href: "/reviews",
    icon: <Star size={20} />,
    children: [
      { label: "Solicitações", href: "/reviews", icon: <ClipboardList size={16} /> },
      { label: "Respostas IA", href: "/reviews/responses", icon: <MessageCircle size={16} /> },
      { label: "Feedback", href: "/reviews/feedback", icon: <AlertTriangle size={16} /> },
    ],
  },
  {
    label: "Chatbot",
    href: "/chatbot",
    icon: <MessageSquare size={20} />,
    children: [
      { label: "Meus Bots", href: "/chatbot", icon: <Bot size={16} /> },
      { label: "Conversas", href: "/chatbot/conversations", icon: <MessageCircle size={16} /> },
      { label: "Contatos", href: "/chatbot/contacts", icon: <Users size={16} /> },
      { label: "Conhecimento", href: "/chatbot/knowledge", icon: <FileText size={16} /> },
    ],
  },
  {
    label: "SEO Local",
    href: "/seo",
    icon: <Search size={20} />,
    children: [
      { label: "Dashboard", href: "/seo", icon: <Globe size={16} /> },
      { label: "Rankings", href: "/seo/rankings", icon: <BarChart3 size={16} /> },
      { label: "Concorrentes", href: "/seo/competitors", icon: <Users size={16} /> },
      { label: "Recomendações", href: "/seo/recommendations", icon: <Lightbulb size={16} /> },
    ],
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: <BarChart3 size={20} />,
  },
  {
    label: "Configurações",
    href: "/settings",
    icon: <Settings size={20} />,
    roles: ["agency_admin", "agency_operator", "clinic_admin"],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, signOut } = useAuth();

  if (!user) return null;

  const filteredNav = navigation.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(user.role);
  });

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col h-screen fixed left-0 top-0">
      {/* Brand */}
      <div className="p-5 border-b border-gray-100">
        <Link href="/">
          <h1 className="text-xl font-bold text-primary-700">
            LK Clinic Tools
          </h1>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto py-4 px-3">
        <ul className="space-y-1">
          {filteredNav.map((item) => {
            const isActive =
              pathname === item.href ||
              pathname.startsWith(item.href + "/");
            const hasChildren = item.children && item.children.length > 0;
            const isParentActive = hasChildren && item.children!.some(
              (child) => pathname === child.href || pathname.startsWith(child.href + "/")
            );

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                    isActive || isParentActive
                      ? "bg-primary-50 text-primary-700"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                  )}
                >
                  {item.icon}
                  {item.label}
                </Link>

                {/* Sub-navigation */}
                {hasChildren && (isActive || isParentActive) && (
                  <ul className="ml-8 mt-1 space-y-0.5">
                    {item.children!.map((child) => (
                      <li key={child.href}>
                        <Link
                          href={child.href}
                          className={cn(
                            "flex items-center gap-2 px-3 py-2 rounded-md text-xs font-medium transition-colors",
                            pathname === child.href
                              ? "text-primary-700 bg-primary-50/50"
                              : "text-gray-500 hover:text-gray-700"
                          )}
                        >
                          {child.icon}
                          {child.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      {/* User / Logout */}
      <div className="p-4 border-t border-gray-100">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center text-primary-700 text-sm font-semibold">
            {user.name?.[0]?.toUpperCase() || "U"}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">
              {user.name}
            </p>
            <p className="text-xs text-gray-500 truncate">{user.email}</p>
          </div>
        </div>
        <button
          onClick={signOut}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-red-600 transition-colors w-full px-2 py-1.5"
        >
          <LogOut size={16} />
          Sair
        </button>
      </div>
    </aside>
  );
}

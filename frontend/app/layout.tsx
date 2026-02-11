import type { Metadata } from "next";
import { Toaster } from "react-hot-toast";
import "./globals.css";

export const metadata: Metadata = {
  title: "LK Clinic Tools",
  description:
    "Plataforma de automação para clínicas - Agendamentos, Avaliações, Chatbot e SEO",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              borderRadius: "8px",
              background: "#333",
              color: "#fff",
              fontSize: "14px",
            },
          }}
        />
        {children}
      </body>
    </html>
  );
}

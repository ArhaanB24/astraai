import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { AuthProvider } from "@/lib/AuthContext";

export const metadata = {
  title: "ArthaAI - Multi-Agent Financial AI Platform",
  description: "Unified Multi-Agent AI Platform for Personal Financial Advisory & Mutual Fund Management",
  icons: {
    icon: "/icon.png",
    shortcut: "/icon.png",
    apple: "/icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="flex min-h-screen bg-background text-gray-100">
        <AuthProvider>
          <Sidebar />
          <main className="flex-1 p-6 overflow-y-auto">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}

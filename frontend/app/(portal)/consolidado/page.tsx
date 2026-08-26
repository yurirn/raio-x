import type { Metadata } from "next";
import { DashboardView } from "@/components/dashboard-view";

export const metadata: Metadata = { title: "Consolidado" };
export default function ConsolidatedPage() { return <DashboardView />; }

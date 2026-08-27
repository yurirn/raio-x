export type YesNo = "YES" | "NO";
export type Role = "ADMIN" | "COORDINATOR" | "OPERATOR";

export interface NamedEntity {
  id: number;
  name: string;
  active?: boolean;
  regional_id?: number;
  coordinator_id?: number;
  store_id?: number;
}

export interface User {
  id: number;
  name: string;
  email: string;
  role: Role;
  active?: boolean;
  can_edit_password_number: boolean;
  store_context: StoreContext | null;
}

export interface StoreContext {
  regional_id: number;
  regional_name: string;
  coordinator_id: number;
  coordinator_name: string;
  store_id: number;
  store_name: string;
}

export interface Attendance {
  id: number;
  date: string;
  password_number: number;
  cpf_cnpj: string;
  current_plan: string | null;
  ftth_available: YesNo;
  available_for_sale: YesNo;
  sale: YesNo;
  reason_id: number | null;
  consultant_id: number;
  store_id: number;
  coordinator_id: number;
  regional_id: number;
  created_at: string;
  updated_at: string;
}

export interface Performance {
  consultant_id: number;
  consultant: string;
  passwords: number;
  ftth_available: number;
  available_for_sale: number;
  sales: number;
  share_passwords: number;
  availability_percentage: number;
  availability_real_percentage: number;
  conversion: number;
  position: number;
}

export interface StorePerformance extends Omit<Performance, "consultant_id" | "consultant"> {
  store_id: number;
  store: string;
}

export interface DashboardData {
  cards: {
    passwords: number;
    ftth_available: number;
    available_for_sale: number;
    sales: number;
    conversion: number;
    active_consultants: number;
  };
  performance: Performance[];
  store_performance: StorePerformance[];
  ranking: Performance[];
  daily: Array<{ date: string; passwords: number; sales: number; available: number; conversion: number }>;
  reasons: Array<{ reason: string; count: number }>;
}

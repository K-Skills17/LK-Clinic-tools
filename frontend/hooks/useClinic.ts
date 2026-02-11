/**
 * LK Clinic Tools - Clinic Hook
 * Provides clinic context for API calls with tenant isolation.
 */

"use client";

import { useAuth } from "./useAuth";
import { api } from "@/lib/api";

export function useClinic() {
  const { user, isAgency } = useAuth();
  const clinicId = user?.clinic_id;

  function clinicUrl(path: string): string {
    if (!clinicId) throw new Error("No clinic context");
    return `/clinics/${clinicId}${path}`;
  }

  async function fetchClinicData<T>(path: string): Promise<T> {
    return api.get<T>(clinicUrl(path));
  }

  async function postClinicData<T>(path: string, body?: unknown): Promise<T> {
    return api.post<T>(clinicUrl(path), body);
  }

  async function patchClinicData<T>(path: string, body?: unknown): Promise<T> {
    return api.patch<T>(clinicUrl(path), body);
  }

  async function deleteClinicData<T>(path: string): Promise<T> {
    return api.delete<T>(clinicUrl(path));
  }

  return {
    clinicId,
    isAgency,
    clinicUrl,
    fetchClinicData,
    postClinicData,
    patchClinicData,
    deleteClinicData,
  };
}

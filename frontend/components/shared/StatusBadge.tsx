"use client";

import { getStatusColor, translateStatus } from "@/lib/utils";

interface StatusBadgeProps {
  status: string;
  customLabel?: string;
}

export function StatusBadge({ status, customLabel }: StatusBadgeProps) {
  return (
    <span className={getStatusColor(status)}>
      {customLabel || translateStatus(status)}
    </span>
  );
}

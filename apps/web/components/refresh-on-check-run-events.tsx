"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

type Props =
  | { requestId: string; promotionId?: never; active: boolean }
  | { requestId?: never; promotionId: string; active: boolean };

export function RefreshOnCheckRunEvents(props: Props) {
  const router = useRouter();

  useEffect(() => {
    if (!props.active) {
      return;
    }

    const fallbackTimer = window.setInterval(() => {
      router.refresh();
    }, 5000);

    return () => {
      window.clearInterval(fallbackTimer);
    };
  }, [props.active, router]);

  return null;
}

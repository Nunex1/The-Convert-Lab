import type { ReactNode } from "react";

// One accessible DOM: CSS reorders the controls above the monitor on small screens.
export function MobileConverter({ children }: { children: ReactNode }) {
  return <div className="converter-device">{children}</div>;
}

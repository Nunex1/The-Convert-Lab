import { ArrowUpRight, ShieldCheck } from "lucide-react";
import type { ConverterState } from "@/hooks/use-converter";
import { StatusLens } from "./status-lens";
import { StatusIndicators } from "./status-indicators";
import { ConversionScreen } from "./conversion-screen";

export function DeviceLeftPanel({ state }: { state: ConverterState }) {
  return (
    <section
      className="device-panel left-panel"
      aria-label="Monitor de conversão"
    >
      <div className="left-hardware-header">
        <div className="hardware-signals">
          <StatusLens
            phase={state.phase}
            online={state.connection === "online"}
          />
          <StatusIndicators phase={state.phase} />
        </div>
        <span className="hardware-model">
          CL<span> / </span>01
        </span>
      </div>
      <div className="screen-bezel">
        <ConversionScreen state={state} />
      </div>
      <div className="hardware-footer">
        <span>
          <ShieldCheck size={15} /> SEM ARMAZENAMENTO PERMANENTE
        </span>
        <a href="#como-funciona" aria-label="Saiba como funciona">
          Guia rápido <ArrowUpRight size={14} />
        </a>
      </div>
    </section>
  );
}

"use client";
import { useConverter } from "@/hooks/use-converter";
import { DeviceLeftPanel } from "./device-left-panel";
import { DeviceRightPanel } from "./device-right-panel";
import { MobileConverter } from "./mobile-converter";

export function ConverterDevice() {
  const state = useConverter();
  return (
    <div className="device-stage" id="conversor">
      <MobileConverter>
        <DeviceRightPanel state={state} />
        <div className="device-hinge" aria-hidden="true">
          <span />
          <i />
          <span />
        </div>
        <DeviceLeftPanel state={state} />
      </MobileConverter>
      <div className="device-caption">
        <span>
          <i /> FERRAMENTA SIMPLES. POSSIBILIDADES INFINITAS.
        </span>
        <span>CONVERTLAB / DOCUMENT CONVERTER</span>
      </div>
    </div>
  );
}

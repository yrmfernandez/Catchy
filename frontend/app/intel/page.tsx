import { Placeholder } from "@/components/Placeholder";

export default function IntelPage() {
  return (
    <Placeholder
      title="Threat intelligence"
      description="Provider status and reputation lookups (VirusTotal, URLScan, RDAP, HIBP) are implemented in the backend and already feed every scan — per-scan results appear in the scan view. A dedicated browsing surface isn't built yet."
      milestone="M9"
    />
  );
}

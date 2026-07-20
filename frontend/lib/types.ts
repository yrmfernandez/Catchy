// TypeScript mirrors of the backend Pydantic schemas. Keeping these explicit
// (rather than `any`) is what makes the UI refactor-safe when the API evolves.

export type Band = "low" | "medium" | "high" | "critical";
export type Severity = "info" | "low" | "medium" | "high" | "critical";

export interface EmailAddress {
  raw: string;
  name: string | null;
  address: string | null;
  domain: string | null;
}

export interface AuthResults {
  spf: string | null;
  dkim: string | null;
  dmarc: string | null;
  dkim_signature_present: boolean;
  raw: string | null;
}

export interface ExtractedUrl {
  url: string;
  scheme: string | null;
  host: string | null;
  domain: string | null;
  is_ip: boolean;
  in_html: boolean;
  anchor_text: string | null;
  anchor_mismatch: boolean;
}

export interface Attachment {
  filename: string | null;
  content_type: string | null;
  extension: string | null;
  size_bytes: number;
  sha256: string | null;
}

export interface ParsedEmail {
  subject: string | null;
  from: EmailAddress | null;
  reply_to: EmailAddress | null;
  to: EmailAddress[];
  return_path: string | null;
  date: string | null;
  message_id: string | null;
  auth: AuthResults;
  urls: ExtractedUrl[];
  attachments: Attachment[];
  has_html: boolean;
  has_plain: boolean;
  body_plain: string | null;
  body_html: string | null;
  header_count: number;
  received_count: number;
  reply_to_mismatch: boolean;
}

export interface FeatureVector {
  url_count: number;
  unique_domain_count: number;
  ip_url_count: number;
  link_mismatch_count: number;
  max_domain_entropy: number;
  spf_fail: boolean;
  dkim_missing: boolean;
  dmarc_fail: boolean;
  reply_to_mismatch: boolean;
  attachment_count: number;
  risky_attachment_count: number;
  suspicious_keyword_count: number;
  urgency_score: number;
  capital_ratio: number;
  exclamation_count: number;
  html_ratio: number;
  body_length: number;
}

export interface Indicator {
  id: string;
  title: string;
  category: string;
  severity: Severity;
  points: number;
  detail: string;
}

export interface RiskAssessment {
  score: number;
  band: Band;
  summary: string;
  indicators: Indicator[];
}

export interface MLPrediction {
  available: boolean;
  probability: number | null;
  label: string | null;
  model_type: string | null;
  threshold: number | null;
}

export interface ProviderStatus {
  name: string;
  status: string;
  detail: string | null;
}

export interface ThreatIntel {
  enabled: boolean;
  available: boolean;
  providers: ProviderStatus[];
  indicators: Indicator[];
  url_malicious_hits: number;
  attachment_malicious_hits: number;
  min_domain_age_days: number | null;
  sender_breach_count: number | null;
}

export interface LlmAnalysis {
  available: boolean;
  provider: string | null;
  model: string | null;
  summary: string | null;
  why_suspicious: string[];
  attack_techniques: string[];
  recommendations: string[];
  confidence: number | null;
  error: string | null;
}

export interface FusionComponent {
  name: string;
  score: number;
  weight: number;
}

export interface FusionResult {
  score: number;
  band: Band;
  method: string;
  critical_override: boolean;
  components: FusionComponent[];
  summary: string;
}

export interface ScanResult {
  parsed: ParsedEmail;
  features: FeatureVector;
  assessment: RiskAssessment;
  ml: MLPrediction;
  intel: ThreatIntel;
  analysis: LlmAnalysis;
  fusion: FusionResult;
}

// ---- Auth + history ----

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ScanSummary {
  id: string;
  created_at: string;
  score: number;
  band: Band;
  method: string;
  subject: string | null;
  sender_domain: string | null;
}

export interface ScanRecord {
  id: string;
  created_at: string;
  result: ScanResult;
}

export interface ScanDiff {
  score_delta: number;
  band_from: string;
  band_to: string;
  indicators_added: string[];
  indicators_removed: string[];
}

export interface CompareResult {
  a: ScanRecord;
  b: ScanRecord;
  diff: ScanDiff;
}

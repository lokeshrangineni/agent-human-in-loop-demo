export interface UserInfo {
  id: string;
  name: string;
  role: 'admin' | 'user';
}

export interface ExtractedField {
  value: string | number | null;
  confidence: number;
  original_text?: string;
}

export interface ExtractionResult {
  header_fields: Record<string, ExtractedField>;
  line_items: Array<Record<string, ExtractedField>>;
  summary_fields: Record<string, ExtractedField>;
  raw_text?: string;
  extraction_notes: string[];
}

export interface ValidationRule {
  rule_name: string;
  passed: boolean;
  severity: 'info' | 'warning' | 'error';
  message: string;
}

export interface ValidationResult {
  rules: ValidationRule[];
  overall_recommendation: 'approve' | 'reject' | 'review' | 'pending';
  overall_confidence: number;
  validation_notes: string[];
}

export interface Invoice {
  id: string;
  file_name: string;
  status: string;
  uploaded_by: string;
  extraction_result: ExtractionResult | null;
  validation_result: ValidationResult | null;
  overall_confidence: number | null;
  page_count: number;
  extraction_prompt_version: number | null;
  validation_prompt_version: number | null;
  created_at: string;
  updated_at: string;
}

export interface InvoiceListItem {
  id: string;
  file_name: string;
  status: string;
  uploaded_by: string;
  overall_confidence: number | null;
  vendor_name: string | null;
  invoice_number: string | null;
  total_amount: number | null;
  created_at: string;
}

export interface ApprovalRequest {
  id: string;
  invoice_id: string;
  request_type: string;
  requested_by: string;
  proposed_changes: Record<string, unknown>;
  status: string;
  reviewed_by: string | null;
  admin_notes: string | null;
  final_changes: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface FeedbackItem {
  id: string;
  invoice_id: string | null;
  vendor_name: string | null;
  field_name: string | null;
  original_value: string | null;
  corrected_value: string | null;
  feedback_text: string;
  submitted_by: string;
  status: string;
  reviewed_by: string | null;
  created_at: string;
}

export interface PromptVersion {
  id: string;
  prompt_key: string;
  version: number;
  content: string;
  change_summary: string;
  created_by: string;
  is_active: number;
  created_at: string;
}

export interface PromptSummary {
  prompt_key: string;
  description: string;
  active_version: PromptVersion | null;
  total_versions: number;
}

export interface PromptDetail {
  prompt_key: string;
  active_content: string;
  active_version: PromptVersion | null;
  versions: PromptVersion[];
}

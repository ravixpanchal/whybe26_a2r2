"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { downloadReport } from "@/lib/api";
import type {
  BorrowerInput,
  ExplanationResponse,
  SimulatorResponse,
} from "@/types/assessment";

export function DownloadReportButton({
  explanation,
  borrowerInput,
  simulator,
}: {
  explanation: ExplanationResponse;
  borrowerInput: BorrowerInput;
  simulator?: SimulatorResponse;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleDownload = async () => {
    setLoading(true);
    setError("");
    try {
      const blob = await downloadReport({
        explanation,
        borrower_input: borrowerInput,
        simulator,
      });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "credilens-assessment.pdf";
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Report generation failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Button type="button" variant="outline" onClick={handleDownload} disabled={loading}>
        {loading ? "Preparing report…" : "Download PDF report"}
      </Button>
      {error && <p role="alert" className="mt-2 text-xs font-semibold text-red-700">{error}</p>}
    </div>
  );
}

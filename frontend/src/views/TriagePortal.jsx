import React, { useState, useEffect } from 'react';
import { LiveTicketForm } from '../components/triage/LiveTicketForm';
import { PredictionResultCard } from '../components/triage/PredictionResultCard';
import { ProbabilityBreakdown } from '../components/triage/ProbabilityBreakdown';
import { CustomerProfileCard } from '../components/triage/CustomerProfileCard';
import { BatchTriageModal } from '../components/triage/BatchTriageModal';
import { Button } from '../components/common/Button';
import { useDebounce } from '../hooks/useDebounce';
import { predictTicket } from '../services/api';
import { Layers, CheckCircle2 } from 'lucide-react';

export const TriagePortal = ({ onTicketSubmitted }) => {
  const [title, setTitle] = useState("Database connection pool timeout");
  const [text, setText] = useState("Production PostgreSQL database connection pool exhausted with timeout errors on primary replica. Queries failing across API gateways.");
  const [customerId, setCustomerId] = useState("CUST-1001");
  const [urgencyHint, setUrgencyHint] = useState("Critical");

  const [predictionResult, setPredictionResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isBatchOpen, setIsBatchOpen] = useState(false);
  const [submittedToast, setSubmittedToast] = useState(false);

  // Debounce the text & title input for live inference
  const debouncedText = useDebounce(text, 350);
  const debouncedTitle = useDebounce(title, 350);

  useEffect(() => {
    if (!debouncedText.trim()) {
      setPredictionResult(null);
      return;
    }

    let isMounted = true;
    const runInference = async () => {
      setIsLoading(true);
      try {
        const payload = {
          title: debouncedTitle,
          text: debouncedText,
          customer_id: customerId || null,
          urgency_hint: urgencyHint || null
        };
        const data = await predictTicket(payload);
        if (isMounted) {
          setPredictionResult(data);
        }
      } catch (err) {
        console.error("Inference error:", err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    runInference();
    return () => { isMounted = false; };
  }, [debouncedText, debouncedTitle, customerId, urgencyHint]);

  const handleSubmit = () => {
    if (!predictionResult) return;
    if (onTicketSubmitted) {
      onTicketSubmitted({
        ...predictionResult,
        title,
        text,
        customer_id: customerId,
        submittedAt: new Date().toISOString()
      });
    }
    setSubmittedToast(true);
    setTimeout(() => setSubmittedToast(false), 4000);
  };

  const handleReset = () => {
    setTitle("");
    setText("");
    setCustomerId("CUST-1001");
    setUrgencyHint("");
    setPredictionResult(null);
  };

  return (
    <div className="space-y-6">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            Real-Time AI Triage Workspace
          </h2>
          <p className="text-xs text-slate-400">
            Debounced continuous NLP inference powered by fine-tuned DistilBERT and Feast online features
          </p>
        </div>

        <Button
          variant="secondary"
          size="md"
          icon={Layers}
          onClick={() => setIsBatchOpen(true)}
        >
          Batch JSON Triage
        </Button>
      </div>

      {/* Success Notification Toast */}
      {submittedToast && (
        <div className="p-4 rounded-xl bg-emerald-500/15 border border-emerald-500/40 text-emerald-300 flex items-center justify-between shadow-glow-cyan animate-in fade-in slide-in-from-top-4 duration-300">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <div>
              <span className="font-bold text-sm">Ticket Successfully Routed!</span>
              <p className="text-xs text-slate-300">Ticket was logged to SQLite WAL telemetry and dispatched to the {predictionResult?.assigned_team}.</p>
            </div>
          </div>
        </div>
      )}

      {/* 2-Column Triage Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Interactive Form */}
        <div className="lg:col-span-6 space-y-6">
          <LiveTicketForm
            title={title}
            setTitle={setTitle}
            text={text}
            setText={setText}
            customerId={customerId}
            setCustomerId={setCustomerId}
            urgencyHint={urgencyHint}
            setUrgencyHint={setUrgencyHint}
            onSubmit={handleSubmit}
            onReset={handleReset}
            isLoading={isLoading}
          />

          <CustomerProfileCard
            customerId={customerId}
            features={predictionResult?.customer_features}
          />
        </div>

        {/* Right Column: Live AI Triage & Probability Insights */}
        <div className="lg:col-span-6 space-y-6">
          <PredictionResultCard
            result={predictionResult}
            isLoading={isLoading && !predictionResult}
          />

          <ProbabilityBreakdown
            probabilities={predictionResult?.probabilities}
            predictedCategory={predictionResult?.predicted_category}
          />
        </div>
      </div>

      {/* Batch Modal */}
      <BatchTriageModal
        isOpen={isBatchOpen}
        onClose={() => setIsBatchOpen(false)}
        onBatchSuccess={(data) => {
          if (onTicketSubmitted && data?.predictions) {
            data.predictions.forEach(p => onTicketSubmitted({ ...p, submittedAt: new Date().toISOString() }));
          }
        }}
      />
    </div>
  );
};

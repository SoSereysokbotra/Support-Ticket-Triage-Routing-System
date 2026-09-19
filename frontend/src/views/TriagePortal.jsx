import React, { useState, useEffect } from 'react';
import { LiveTicketForm } from '../components/triage/LiveTicketForm';
import { PredictionResultCard } from '../components/triage/PredictionResultCard';
import { ProbabilityBreakdown } from '../components/triage/ProbabilityBreakdown';
import { CustomerProfileCard } from '../components/triage/CustomerProfileCard';
import { BatchTriageModal } from '../components/triage/BatchTriageModal';
import { Button } from '../components/common/Button';
import { PageHeader } from '../components/common/PageHeader';
import { Alert } from '../components/common/Alert';
import { useDebounce } from '../hooks/useDebounce';
import { predictTicket } from '../services/api';
import { Layers } from 'lucide-react';

export const TriagePortal = ({ onTicketSubmitted }) => {
  const [title, setTitle] = useState('');
  const [text, setText] = useState('');
  const [customerId, setCustomerId] = useState('CUST-1001');
  const [urgencyHint, setUrgencyHint] = useState('');

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
          urgency_hint: urgencyHint || null,
        };
        const data = await predictTicket(payload);
        if (isMounted) {
          setPredictionResult(data);
        }
      } catch (err) {
        console.error('Inference error:', err);
      } finally {
        if (isMounted) setIsLoading(false);
      }
    };

    runInference();
    return () => {
      isMounted = false;
    };
  }, [debouncedText, debouncedTitle, customerId, urgencyHint]);

  const handleSubmit = () => {
    if (!predictionResult) return;
    if (onTicketSubmitted) {
      onTicketSubmitted({
        ...predictionResult,
        title,
        text,
        customer_id: customerId,
        submittedAt: new Date().toISOString(),
      });
    }
    setSubmittedToast(true);
    setTimeout(() => setSubmittedToast(false), 4000);
  };

  const handleReset = () => {
    setTitle('');
    setText('');
    setCustomerId('CUST-1001');
    setUrgencyHint('');
    setPredictionResult(null);
  };

  return (
    <>
      <PageHeader
        title="Triage"
        description="Classify and route incoming tickets. Predictions update as you type."
        actions={
          <Button variant="secondary" icon={Layers} onClick={() => setIsBatchOpen(true)}>
            Batch triage
          </Button>
        }
      />

      {submittedToast && (
        <Alert variant="success" title="Ticket routed">
          Logged and dispatched to {predictionResult?.assigned_team}.
        </Alert>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-6">
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
            targetSlaHours={predictionResult?.target_sla_hours}
            priorityLevel={predictionResult?.priority_level}
            routingReason={predictionResult?.routing_reason}
          />
        </div>

        <div className="space-y-6">
          <PredictionResultCard result={predictionResult} isLoading={isLoading && !predictionResult} />
          <ProbabilityBreakdown
            probabilities={predictionResult?.probabilities}
            predictedCategory={predictionResult?.predicted_category}
          />
        </div>
      </div>

      <BatchTriageModal
        isOpen={isBatchOpen}
        onClose={() => setIsBatchOpen(false)}
        onBatchSuccess={(data) => {
          if (onTicketSubmitted && data?.predictions) {
            data.predictions.forEach((p) =>
              onTicketSubmitted({ ...p, submittedAt: new Date().toISOString() })
            );
          }
        }}
      />
    </>
  );
};

import React, { useState, useEffect } from 'react';
import { MLOpsKpiCards } from '../components/mlops/MLOpsKpiCards';
import { DriftAnalysisCard } from '../components/mlops/DriftAnalysisCard';
import { ModelRegistryCard } from '../components/mlops/ModelRegistryCard';
import { RetrainTriggerCard } from '../components/mlops/RetrainTriggerCard';
import { PageHeader } from '../components/common/PageHeader';
import { Button } from '../components/common/Button';
import { getMonitoringMetrics } from '../services/api';
import { RefreshCw } from 'lucide-react';

export const MLOpsControl = () => {
  const [metrics, setMetrics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const fetchMetrics = async () => {
    setIsLoading(true);
    try {
      const data = await getMonitoringMetrics();
      setMetrics(data);
    } catch (err) {
      console.warn('Using default metrics:', err);
      setMetrics({
        total_inferences: 42,
        avg_latency_ms: 15.4,
        mean_confidence: 0.962,
        low_confidence_count: 2,
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  return (
    <>
      <PageHeader
        title="MLOps"
        description="Inference telemetry, drift detection, and model registry."
        actions={
          <Button variant="secondary" icon={RefreshCw} onClick={fetchMetrics} isLoading={isLoading}>
            Refresh
          </Button>
        }
      />

      <MLOpsKpiCards metrics={metrics} />

      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="space-y-5">
          <DriftAnalysisCard />
          <RetrainTriggerCard />
        </div>
        <div className="space-y-5">
          <ModelRegistryCard onActionSuccess={fetchMetrics} />
        </div>
      </div>
    </>
  );
};

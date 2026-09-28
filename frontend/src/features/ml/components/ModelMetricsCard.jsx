import FeatureImportanceChart from "./FeatureImportanceChart";
import CalibrationChart from "./CalibrationChart";
import BaselineComparison from "./BaselineComparison";
import TrainTestComparison from "./TrainTestComparison";
import ConfusionMatrixTable from "./ConfusionMatrixTable";
import RocChart from "./RocChart";

function MetricStat({ label, value }) {
  return (
    <div className="text-center">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-lg font-bold text-foreground">{(value * 100).toFixed(1)}%</div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="mt-4 border-t border-border pt-4">
      <div className="mb-2 text-xs font-medium text-muted-foreground">{title}</div>
      {children}
    </div>
  );
}

function ModelMetricsCard({ panel }) {
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="mb-3 flex items-center justify-between">
        <span className="text-sm font-semibold uppercase tracking-wide text-foreground">
          {panel.model_name.replace(/_/g, " ")}
        </span>
        <span className="text-xs text-muted-foreground">
          {panel.n_train} train / {panel.n_test} test
        </span>
      </div>

      <div className="grid grid-cols-4 gap-2 border-b border-border pb-4">
        <MetricStat label="Accuracy" value={panel.metrics.accuracy} />
        <MetricStat label="Precision" value={panel.metrics.precision} />
        <MetricStat label="Recall" value={panel.metrics.recall} />
        <MetricStat label="F1" value={panel.metrics.f1} />
      </div>

      <Section title="Baseline (does it beat always predicting the majority class?)">
        <BaselineComparison modelAccuracy={panel.metrics.accuracy} baselineAccuracy={panel.baseline_accuracy} />
      </Section>

      <Section title="Train vs Test (is it memorizing instead of generalizing?)">
        <TrainTestComparison trainMetrics={panel.train_metrics} testMetrics={panel.metrics} />
      </Section>

      <Section title="Confusion matrix (test set)">
        <ConfusionMatrixTable confusion={panel.confusion} />
      </Section>

      <Section title="ROC curve (ability to discriminate Green/Red)">
        <RocChart roc={panel.roc} />
      </Section>

      <Section title="Feature importance (top 15)">
        <FeatureImportanceChart features={panel.top_features} />
      </Section>

      <Section title="Calibration (predicted probability vs. actual hit rate, by decile)">
        <CalibrationChart calibration={panel.calibration} />
      </Section>
    </div>
  );
}

export default ModelMetricsCard;

import FeatureWorkbench from "@/components/feature/FeatureWorkbench";
import MobileCapturePanel from "@/components/feature/MobileCapturePanel";
import { FEATURE_CONFIGS } from "@/lib/featureConfigs";

export default function Page() {
  const config = FEATURE_CONFIGS.mobile_receipts;
  return <FeatureWorkbench config={config} header={<MobileCapturePanel config={config} />} />;
}

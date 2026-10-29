import FeatureWorkbench from "@/components/feature/FeatureWorkbench";
import OfflineSyncPanel from "@/components/feature/OfflineSyncPanel";
import { FEATURE_CONFIGS } from "@/lib/featureConfigs";

export default function Page() {
  const config = FEATURE_CONFIGS.offline_sync;
  return <FeatureWorkbench config={config} header={<OfflineSyncPanel config={config} />} />;
}

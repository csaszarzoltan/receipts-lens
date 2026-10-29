import FeatureWorkbench from "@/components/feature/FeatureWorkbench";
import { FEATURE_CONFIGS } from "@/lib/featureConfigs";

export default function Page() {
  return <FeatureWorkbench config={FEATURE_CONFIGS.data_quality} />;
}

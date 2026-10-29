"use client";
import AppShell from '@/components/AppShell';
import OnboardingFlow from '@/components/OnboardingFlow';
import PhotoBanner from '@/components/PhotoBanner';
import {useTranslation} from '@/lib/i18n';
export default function OnboardingPage(){const {t}=useTranslation();return <AppShell><div className="mx-auto max-w-xl space-y-6"><PhotoBanner photo="bakery" title={t('onboardingStart')}/><section className="card p-5 sm:p-8"><OnboardingFlow/></section></div></AppShell>}

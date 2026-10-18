"use client";
import AppShell from '@/components/AppShell';
import OnboardingFlow from '@/components/OnboardingFlow';
import {useTranslation} from '@/lib/i18n';
export default function OnboardingPage(){const {t}=useTranslation();return <AppShell><section className="card mx-auto max-w-xl p-5 sm:p-8"><h1 className="mb-5 text-2xl font-bold">{t('onboardingStart')}</h1><OnboardingFlow/></section></AppShell>}

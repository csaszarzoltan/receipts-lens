"use client";

import { useEffect, useRef, useState } from "react";
import { useDialogFocus } from "@/lib/hooks/useDialogFocus";
import { cx } from "@/lib/utils";
import { useTranslation } from "@/lib/i18n";
import { assessCanvas, assessImageQuality, type QualityIssue } from "@/lib/imageQuality";
import { autoCropFile, receiptBoxFromCanvas } from "@/lib/imageCrop";

interface DropZoneProps {
  onFiles: (files: File[]) => void;
  disabled?: boolean;
  label?: string;
}

/**
 * Drag-and-drop + click + camera capture upload area.
 * Camera capture uses navigator.mediaDevices.getUserMedia when available and
 * falls back to an `<input capture>` file picker otherwise.
 */
export default function DropZone({ onFiles, disabled, label }: DropZoneProps) {
  const { t } = useTranslation();
  const dropLabel = label ?? t("dropzoneLabel");
  const [dragging, setDragging] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [cameraPending, setCameraPending] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [capturing, setCapturing] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const cameraInput = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const mounted = useRef(true);
  const cameraSession = useRef(0);
  const pendingRef = useRef(false);
  const captureRef = useRef(false);
  const [held, setHeld] = useState<{ files: File[]; reason: QualityIssue } | null>(null);
  const heldCapture = useRef<{ file: File; reason: QualityIssue } | null>(null);

  const dialogRef = useDialogFocus(cameraOpen, stopCamera);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      cameraSession.current++;
      streamRef.current?.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    };
  }, []);

  async function handleFiles(list: FileList | null) {
    if (!list || list.length === 0) return;
    const files = Array.from(list);
    const results = await Promise.all(files.map(assessImageQuality));
    if (!mounted.current) return;
    const good = files.filter((_, i) => results[i].ok);
    const bad = files.filter((_, i) => !results[i].ok);
    if (good.length) {
      const cropped = await Promise.all(good.map(autoCropFile));
      if (!mounted.current) return;
      onFiles(cropped);
    }
    if (bad.length) setHeld({ files: bad, reason: results.find(r => !r.ok)?.reason ?? "blurry" });
  }

  function uploadHeldAnyway() {
    if (!held) return;
    const files = held.files;
    setHeld(null);
    void Promise.all(files.map(autoCropFile)).then(cropped => { if (mounted.current) onFiles(cropped); });
  }

  function retakeHeld() {
    setHeld(null);
    void openCamera();
  }

  function uploadCaptureAnyway() {
    const pending = heldCapture.current;
    if (!pending) return;
    heldCapture.current = null;
    stopCamera();
    onFiles([pending.file]);
  }

  async function openCamera() {
    if (disabled || pendingRef.current || streamRef.current) return;
    setCameraError(null);
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      // Fall back to the native camera picker (mobile).
      cameraInput.current?.click();
      return;
    }
    const session = ++cameraSession.current;
    pendingRef.current = true;
    setCameraPending(true);
    setCameraReady(false);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      if (!mounted.current || session !== cameraSession.current) {
        stream.getTracks().forEach(track => track.stop());
        return;
      }
      streamRef.current = stream;
      setCameraOpen(true);
      // Attach after render.
      requestAnimationFrame(() => {
        if (mounted.current && session === cameraSession.current && videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => undefined);
        }
      });
    } catch {
      if (!mounted.current || session !== cameraSession.current) return;
      setCameraError(t("dropCameraUnavailable"));
      cameraInput.current?.click();
    } finally {
      if (mounted.current && session === cameraSession.current) {
        pendingRef.current = false;
        setCameraPending(false);
      }
    }
  }

  function stopCamera() {
    heldCapture.current = null;
    cameraSession.current++;
    pendingRef.current = false;
    captureRef.current = false;
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraOpen(false);
    setCameraPending(false);
    setCameraReady(false);
    setCapturing(false);
  }

  function capturePhoto() {
    const video = videoRef.current;
    if (!video || !streamRef.current || video.videoWidth === 0 || captureRef.current) return;
    const session = cameraSession.current;
    captureRef.current = true;
    setCapturing(true);
    setCameraError(null);
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const failed = () => {
      if (!mounted.current || session !== cameraSession.current) return;
      captureRef.current = false;
      setCapturing(false);
      setCameraError(t("dropCaptureFailed"));
    };
    try {
      const context = canvas.getContext("2d");
      if (!context) { failed(); return; }
      context.drawImage(video, 0, 0);
      const quality = assessCanvas(canvas);
      const box = receiptBoxFromCanvas(canvas);
      let target: HTMLCanvasElement = canvas;
      if (box) {
        const cropped = document.createElement("canvas");
        cropped.width = box.width; cropped.height = box.height;
        const croppedContext = cropped.getContext("2d");
        if (croppedContext) {
          croppedContext.drawImage(canvas, box.x, box.y, box.width, box.height, 0, 0, box.width, box.height);
          target = cropped;
        }
      }
      target.toBlob((blob) => {
        if (!mounted.current || session !== cameraSession.current) return;
        if (!blob) { failed(); return; }
        const file = new File([blob], `receipt-${Date.now()}.jpg`, { type: "image/jpeg" });
        if (!quality.ok && quality.reason) {
          // Keep the camera open: retaking is one tap, uploading anyway is explicit.
          heldCapture.current = { file, reason: quality.reason };
          captureRef.current = false;
          setCapturing(false);
          setCameraError(t(quality.reason === "dark" ? "qualityDark" : "qualityBlurry") + " " + t("qualityHint"));
          return;
        }
        heldCapture.current = null;
        stopCamera();
        onFiles([file]);
      }, "image/jpeg", 0.92);
    } catch { failed(); }
  }

  return (
    <div>
      <div className={cx("relative rounded-xl border-2 border-dashed", dragging ? "border-brand-500 bg-brand-50 dark:bg-brand-950" : "border-slate-300 bg-white hover:border-brand-400 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800", disabled && "pointer-events-none opacity-50")}>
        <div
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-disabled={disabled}
          aria-label={dropLabel}
          onClick={() => !disabled && fileInput.current?.click()}
          onKeyDown={(event) => {
            if (!disabled && (event.key === "Enter" || event.key === " ")) {
              event.preventDefault();
              fileInput.current?.click();
            }
          }}
          onDragOver={(event) => {
            event.preventDefault();
            if (!disabled) setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            if (!disabled) handleFiles(event.dataTransfer.files);
          }}
          className="flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-xl px-6 py-10 text-center focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2"
        >
          <svg className="h-10 w-10 text-slate-400 dark:text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <path d="M6 3h12v18l-3-2-3 2-3-2-3 2z" />
            <path d="M9 8h6M9 12h6" />
          </svg>
          <p className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-200">{dropLabel}</p>
          <p className="mt-1 text-xs text-slate-600 dark:text-slate-400">{t("dropFormats")}</p>
        </div>
        {/* Camera capture is a sibling of the dropzone button (not nested) so
            screen readers see two distinct, non-nested interactive controls. */}
        <div className="flex flex-wrap items-center justify-center gap-2 px-6 pb-6">
          <button type="button" disabled={disabled} onClick={() => fileInput.current?.click()} className="btn-primary">
            {t("dropChooseFile")}
          </button>
          <button
            type="button"
            disabled={disabled}
            aria-disabled={!!disabled || cameraPending || cameraOpen}
            onClick={openCamera}
            className="inline-flex min-h-11 items-center rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            {t(cameraPending ? "dropCameraOpening" : "dropTakePhoto")}
          </button>
          {cameraPending ? <button type="button" onClick={stopCamera} className="btn-secondary">{t("dropCancel")}</button> : null}
        </div>
      </div>

      <input
        ref={fileInput}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={(event) => {
          handleFiles(event.target.files);
          event.target.value = "";
        }}
        data-testid="dropzone-input"
      />
      {/* Native camera fallback input */}
      <input
        ref={cameraInput}
        type="file"
        accept="image/*"
        capture="environment"
        className="hidden"
        onChange={(event) => {
          handleFiles(event.target.files);
          event.target.value = "";
        }}
        data-testid="camera-input"
      />

      {held ? (
        <div role="alert" className="mt-3 rounded-xl border border-amber-300 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-100">
          <p className="font-medium">{t("qualityTitle")}</p>
          <p className="mt-1">{t(held.reason === "dark" ? "qualityDark" : "qualityBlurry")} {t("qualityHint")}</p>
          <p className="mt-1 text-xs">{held.files.map(file => file.name).join(", ")}</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button type="button" onClick={retakeHeld} className="btn-primary">{t("dropRetake")}</button>
            <button type="button" onClick={uploadHeldAnyway} className="btn-secondary">{t("dropUploadAnyway")}</button>
          </div>
        </div>
      ) : null}

      {cameraError && !cameraOpen ? (
        <p className="mt-2 text-sm text-amber-700 dark:text-amber-400" role="alert">
          {cameraError}
        </p>
      ) : null}

      {cameraOpen ? (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950/95 p-4" ref={dialogRef} tabIndex={-1} role="dialog" aria-modal="true" aria-label={t("dropTakePhoto")}>
          <video
            ref={videoRef}
            className="max-h-[70vh] w-full max-w-lg rounded-xl bg-black"
            playsInline
            muted
            autoPlay
            onLoadedMetadata={() => setCameraReady(true)}
          />
          {cameraError ? <p role="alert" className="mt-2 text-sm text-white">{cameraError}</p> : null}
          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={capturePhoto}
              disabled={!cameraReady || capturing}
              className="inline-flex min-h-12 items-center rounded-full bg-white px-6 font-medium text-slate-900 disabled:opacity-50"
            >
              📸 {t("dropCapture")}
            </button>
            <button
              type="button"
              onClick={stopCamera}
              className="inline-flex min-h-12 items-center rounded-full bg-slate-700 px-6 font-medium text-white"
            >
              {t("dropCancel")}
            </button>
            {heldCapture.current ? (
              <button type="button" onClick={uploadCaptureAnyway} className="inline-flex min-h-12 items-center rounded-full bg-amber-500 px-6 font-medium text-slate-900">
                {t("dropUploadAnyway")}
              </button>
            ) : null}
          </div>
        </div>
      ) : null}
    </div>
  );
}

"use client";

import { useRef, useState } from "react";
import { cx } from "@/lib/utils";

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
export default function DropZone({ onFiles, disabled, label = "Drag & drop a receipt image here, or click to browse" }: DropZoneProps) {
  const [dragging, setDragging] = useState(false);
  const [cameraOpen, setCameraOpen] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const cameraInput = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  function handleFiles(list: FileList | null) {
    if (!list || list.length === 0) return;
    onFiles(Array.from(list));
  }

  async function openCamera() {
    setCameraError(null);
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
      // Fall back to the native camera picker (mobile).
      cameraInput.current?.click();
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
        audio: false,
      });
      streamRef.current = stream;
      setCameraOpen(true);
      // Attach after render.
      requestAnimationFrame(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          videoRef.current.play().catch(() => undefined);
        }
      });
    } catch {
      setCameraError("Camera unavailable — you can still pick a photo from your device.");
      cameraInput.current?.click();
    }
  }

  function stopCamera() {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    setCameraOpen(false);
  }

  function capturePhoto() {
    const video = videoRef.current;
    if (!video || video.videoWidth === 0) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d")?.drawImage(video, 0, 0);
    canvas.toBlob((blob) => {
      if (blob) onFiles([new File([blob], `receipt-${Date.now()}.jpg`, { type: "image/jpeg" })]);
      stopCamera();
    }, "image/jpeg", 0.92);
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label={label}
        onClick={() => fileInput.current?.click()}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
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
        className={cx(
          "flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-500 focus-visible:ring-offset-2",
          dragging
            ? "border-brand-500 bg-brand-50 dark:bg-brand-950"
            : "border-slate-300 bg-white hover:border-brand-400 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:bg-slate-800",
          disabled && "pointer-events-none opacity-50",
        )}
      >
        <span className="text-4xl" aria-hidden="true">🧾</span>
        <p className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-200">{label}</p>
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">JPG, PNG or WebP — receipts are processed with OCR</p>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
          <span className="inline-flex min-h-9 items-center rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white">
            Choose file
          </span>
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              openCamera();
            }}
            className="inline-flex min-h-9 items-center rounded-lg border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-100 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            📷 Take a photo
          </button>
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

      {cameraError ? (
        <p className="mt-2 text-sm text-amber-600 dark:text-amber-400" role="alert">
          {cameraError}
        </p>
      ) : null}

      {cameraOpen ? (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-slate-950/95 p-4" role="dialog" aria-modal="true" aria-label="Camera capture">
          <video
            ref={videoRef}
            className="max-h-[70vh] w-full max-w-lg rounded-xl bg-black"
            playsInline
            muted
            autoPlay
          />
          <div className="mt-4 flex gap-3">
            <button
              type="button"
              onClick={capturePhoto}
              className="inline-flex min-h-12 items-center rounded-full bg-white px-6 font-medium text-slate-900"
            >
              📸 Capture
            </button>
            <button
              type="button"
              onClick={stopCamera}
              className="inline-flex min-h-12 items-center rounded-full bg-slate-700 px-6 font-medium text-white"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

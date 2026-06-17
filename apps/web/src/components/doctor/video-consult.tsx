"use client";

import { useState } from "react";
import { Video, Mic } from "lucide-react";
import { PrimaryButton } from "@/components/ui/buttons";
import { useLocale } from "@/lib/hooks/use-locale";
import { recordVideoJoined } from "@/lib/api";

const JITSI_ORIGIN = "https://meet.jit.si";

export type VideoMode = "video" | "audio" | "auto";

function resolveMode(mode: VideoMode): "video" | "audio" {
  if (mode === "audio") return "audio";
  if (mode === "video") return "video";
  const conn = (navigator as Navigator & { connection?: { effectiveType?: string } }).connection;
  const slow = conn?.effectiveType === "2g" || conn?.effectiveType === "slow-2g";
  return slow ? "audio" : "video";
}

export function VideoConsult({
  roomName,
  joinLabel = "Join video consultation",
  mode = "auto",
  onJoin,
  appointmentId,
}: {
  roomName: string;
  joinLabel?: string;
  mode?: VideoMode;
  onJoin?: () => void;
  appointmentId?: string;
}) {
  const { t } = useLocale();
  const [open, setOpen] = useState(false);
  const [lowData, setLowData] = useState(false);

  if (!roomName) return null;

  const effective = lowData ? "audio" : resolveMode(mode);
  const config =
    effective === "audio"
      ? "config.startWithVideoMuted=true&config.startAudioOnly=true"
      : "config.resolution=180&config.constraints.video.height.ideal=180";
  const src = `${JITSI_ORIGIN}/${encodeURIComponent(roomName)}#config.prejoinPageEnabled=false&config.startWithAudioMuted=false&${config}`;

  const handleJoin = () => {
    onJoin?.();
    if (appointmentId) {
      void recordVideoJoined(appointmentId).catch(() => undefined);
    }
    setOpen(true);
  };

  return (
    <div className="mt-4">
      {!open ? (
        <div className="space-y-3">
          <label className="flex items-center gap-2 text-sm text-text-muted">
            <input
              type="checkbox"
              checked={lowData}
              onChange={(e) => setLowData(e.target.checked)}
              className="h-4 w-4 rounded border-border"
            />
            <Mic className="h-4 w-4" aria-hidden />
            {t("video.audioOnly")}
          </label>
          <PrimaryButton onClick={handleJoin} className="gap-2">
            <Video className="h-5 w-5" aria-hidden />
            {joinLabel}
          </PrimaryButton>
        </div>
      ) : (
        <div className="overflow-hidden rounded-card border border-border bg-black">
          <iframe
            title="Setu video consultation"
            src={src}
            allow="camera; microphone; fullscreen; display-capture"
            className={`w-full border-0 ${effective === "audio" ? "min-h-[120px]" : "aspect-video min-h-[280px]"}`}
          />
          <button
            type="button"
            onClick={() => setOpen(false)}
            className="w-full bg-surface-raised py-2 text-sm font-semibold text-primary"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
}

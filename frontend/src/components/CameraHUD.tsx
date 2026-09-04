import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Camera,
  Sparkles,
  UserCheck,
  X,
  Maximize2,
  Minimize2,
  Video,
  RefreshCw,
  AlertCircle,
  SwitchCamera,
  Eye,
  EyeOff,
  Crosshair,
  Radio,
  Info,
  Layers,
  HelpCircle
} from 'lucide-react';
import { wsService } from '../services/websocket';

interface CameraHUDProps {
  isActive: boolean;
  isContinuous: boolean;
  onToggleCamera: () => void;
  onClose: () => void;
}

interface VideoDevice {
  deviceId: string;
  label: string;
  isInbuilt: boolean;
  isVirtual: boolean;
}

interface RawDetectionBox {
  name: string;
  confidence: number;
  location?: string;
  spatial_relationship?: string;
  rel_x: number;
  rel_y: number;
  rel_w: number;
  rel_h: number;
}

interface SmoothedBox extends RawDetectionBox {
  id: string;
  lastSeen: number;
  targetClass: string;
}

export const CameraHUD: React.FC<CameraHUDProps> = ({
  isActive,
  isContinuous,
  onToggleCamera,
  onClose
}) => {
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [isExpanded, setIsExpanded] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [permissionState, setPermissionState] = useState<'granted' | 'prompt' | 'denied' | 'pending'>('pending');
  const [errorDetails, setErrorDetails] = useState<string>('');

  const [availableDevices, setAvailableDevices] = useState<VideoDevice[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>(() => {
    return localStorage.getItem('aegis_preferred_camera') || '';
  });

  // Live real-time detections with temporal smoothing
  const [liveBoxes, setLiveBoxes] = useState<SmoothedBox[]>([]);
  const [showLiveDetection, setShowLiveDetection] = useState<boolean>(true);
  const [showTargetDetails, setShowTargetDetails] = useState<boolean>(true);
  const [frameAspectRatio, setFrameAspectRatio] = useState<number>(4 / 3);
  const [activeTargetId, setActiveTargetId] = useState<string | null>(null);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const boxesRef = useRef<SmoothedBox[]>([]);

  // Helper to identify virtual or phone link cameras to deprioritize
  const isPhoneLinkOrVirtual = (label: string): boolean => {
    return /phone\s*link|virtual|obs|droidcam|iriun|epoccam|link|screen|ip\s*cam/i.test(label);
  };

  // Helper to identify physical inbuilt/integrated webcams
  const isInbuiltWebcam = (label: string): boolean => {
    return (
      /integrated|internal|built-in|front|hd\s*webcam|webcam|camera|facetime|easycamera/i.test(label) &&
      !isPhoneLinkOrVirtual(label)
    );
  };

  const getRankedDevices = (devices: MediaDeviceInfo[]): VideoDevice[] => {
    const videoInputs = devices.filter((d) => d.kind === 'videoinput');

    const mapped = videoInputs.map((d, index) => {
      const label = d.label || `Camera ${index + 1}`;
      const inbuilt = isInbuiltWebcam(label);
      const virtual = isPhoneLinkOrVirtual(label);
      return {
        deviceId: d.deviceId,
        label,
        isInbuilt: inbuilt,
        isVirtual: virtual
      };
    });

    // Sort: Inbuilt physical first, then real USB/external cameras, virtual cameras last
    return mapped.sort((a, b) => {
      if (a.isInbuilt && !b.isInbuilt) return -1;
      if (!a.isInbuilt && b.isInbuilt) return 1;
      if (!a.isVirtual && b.isVirtual) return -1;
      if (a.isVirtual && !b.isVirtual) return 1;
      return 0;
    });
  };

  const startWebcam = useCallback(async (forcedDeviceId?: string) => {
    try {
      setErrorDetails('');
      setPermissionState('pending');

      // 1. Initial probe to ensure camera permission and retrieve full device labels
      const initialStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false
      });

      const rawDevices = await navigator.mediaDevices.enumerateDevices();
      const ranked = getRankedDevices(rawDevices);
      setAvailableDevices(ranked);

      // Stop probe stream before binding target
      initialStream.getTracks().forEach((track) => track.stop());

      // 2. Select target device: forced -> saved preference -> top-ranked integrated camera
      let targetDeviceId = forcedDeviceId || selectedDeviceId;

      const deviceExists = ranked.some((d) => d.deviceId === targetDeviceId);
      if (!targetDeviceId || !deviceExists) {
        const preferred = ranked.find((d) => d.isInbuilt) || ranked.find((d) => !d.isVirtual) || ranked[0];
        if (preferred && preferred.deviceId) {
          targetDeviceId = preferred.deviceId;
          setSelectedDeviceId(preferred.deviceId);
          localStorage.setItem('aegis_preferred_camera', preferred.deviceId);
        }
      }

      // 3. Open selected physical camera in high-definition (1280x720)
      const videoConstraints: MediaTrackConstraints = targetDeviceId
        ? {
            deviceId: { exact: targetDeviceId },
            width: { ideal: 1280, min: 640 },
            height: { ideal: 720, min: 480 }
          }
        : {
            width: { ideal: 1280, min: 640 },
            height: { ideal: 720, min: 480 },
            facingMode: 'user'
          };

      const finalStream = await navigator.mediaDevices.getUserMedia({
        video: videoConstraints,
        audio: false
      });

      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop());
      }

      streamRef.current = finalStream;

      if (videoRef.current) {
        videoRef.current.srcObject = finalStream;
        videoRef.current.onloadedmetadata = () => {
          if (videoRef.current && videoRef.current.videoWidth > 0 && videoRef.current.videoHeight > 0) {
            setFrameAspectRatio(videoRef.current.videoWidth / videoRef.current.videoHeight);
          }
          videoRef.current?.play().catch((e) => console.warn('Play error:', e));
        };
      }

      setPermissionState('granted');
    } catch (err: any) {
      console.warn('Webcam startup error:', err);
      setPermissionState('denied');
      setErrorDetails(err.message || 'Could not access camera');
    }
  }, [selectedDeviceId]);

  // Initialize camera stream when active
  useEffect(() => {
    if (!isActive) {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      boxesRef.current = [];
      setLiveBoxes([]);
      return;
    }

    startWebcam();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
    };
  }, [isActive, startWebcam]);

  // Smooth box updates with Exponential Moving Average (EMA) and 850ms persistence buffer
  const updateSmoothedBoxes = useCallback((incomingBoxes: RawDetectionBox[]) => {
    const now = Date.now();
    const current = boxesRef.current;
    const updated: SmoothedBox[] = [];
    const matchedIncoming = new Set<number>();

    // Step 1: Match incoming detections to previous boxes by label & center Euclidean distance
    for (const prev of current) {
      let bestMatchIdx = -1;
      let bestDist = 0.22; // max distance threshold in normalized coords

      const prevCx = prev.rel_x + prev.rel_w / 2;
      const prevCy = prev.rel_y + prev.rel_h / 2;

      incomingBoxes.forEach((inc, idx) => {
        if (matchedIncoming.has(idx)) return;
        if (inc.name.toLowerCase() !== prev.name.toLowerCase()) return;

        const incCx = inc.rel_x + inc.rel_w / 2;
        const incCy = inc.rel_y + inc.rel_h / 2;
        const dist = Math.hypot(incCx - prevCx, incCy - prevCy);

        if (dist < bestDist) {
          bestDist = dist;
          bestMatchIdx = idx;
        }
      });

      if (bestMatchIdx >= 0) {
        matchedIncoming.add(bestMatchIdx);
        const inc = incomingBoxes[bestMatchIdx];
        // EMA smoothing (65% weight on new position, 35% on previous): ultra fluid motion
        const smoothed: SmoothedBox = {
          id: prev.id,
          name: inc.name,
          targetClass: inc.name.toLowerCase(),
          confidence: Number((prev.confidence * 0.3 + inc.confidence * 0.7).toFixed(2)),
          location: inc.location || prev.location,
          spatial_relationship: inc.spatial_relationship || prev.spatial_relationship,
          rel_x: Number((prev.rel_x * 0.35 + inc.rel_x * 0.65).toFixed(4)),
          rel_y: Number((prev.rel_y * 0.35 + inc.rel_y * 0.65).toFixed(4)),
          rel_w: Number((prev.rel_w * 0.35 + inc.rel_w * 0.65).toFixed(4)),
          rel_h: Number((prev.rel_h * 0.35 + inc.rel_h * 0.65).toFixed(4)),
          lastSeen: now
        };
        updated.push(smoothed);
      } else if (now - prev.lastSeen < 850) {
        // Retain box for 850ms across brief frame drops to eliminate flickering
        updated.push(prev);
      }
    }

    // Step 2: Add newly discovered targets
    incomingBoxes.forEach((inc, idx) => {
      if (!matchedIncoming.has(idx)) {
        const newBox: SmoothedBox = {
          id: `${inc.name}_${now}_${Math.random().toString(36).substring(2, 7)}`,
          name: inc.name,
          targetClass: inc.name.toLowerCase(),
          confidence: inc.confidence,
          location: inc.location,
          spatial_relationship: inc.spatial_relationship,
          rel_x: inc.rel_x,
          rel_y: inc.rel_y,
          rel_w: inc.rel_w,
          rel_h: inc.rel_h,
          lastSeen: now
        };
        updated.push(newBox);
      }
    });

    boxesRef.current = updated;
    setLiveBoxes(updated);
  }, []);

  // Periodic pruning of stale targets (older than 850ms)
  useEffect(() => {
    const cleanupInterval = setInterval(() => {
      const now = Date.now();
      const current = boxesRef.current;
      const filtered = current.filter((b) => now - b.lastSeen < 850);
      if (filtered.length !== current.length) {
        boxesRef.current = filtered;
        setLiveBoxes(filtered);
      }
    }, 250);
    return () => clearInterval(cleanupInterval);
  }, []);

  // Subscribe to live WebSocket detections
  useEffect(() => {
    const unsub = wsService.subscribe((data) => {
      if (data.type === 'live_detections') {
        if (data.frame_w && data.frame_h && data.frame_h > 0) {
          setFrameAspectRatio(data.frame_w / data.frame_h);
        }
        updateSmoothedBoxes(data.boxes || []);
      }
    });
    return () => unsub();
  }, [updateSmoothedBoxes]);

  // Continuous frame transmission to backend at 320ms (~3.1 FPS)
  useEffect(() => {
    if (!isActive || permissionState !== 'granted') {
      boxesRef.current = [];
      setLiveBoxes([]);
      return;
    }

    const interval = setInterval(() => {
      captureAndSendFrame(false);
    }, 320);

    return () => clearInterval(interval);
  }, [isActive, permissionState, showLiveDetection]);

  const captureCurrentFrameBase64 = (): string | null => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas && video.videoWidth > 0 && video.videoHeight > 0) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const dataUrl = canvas.toDataURL('image/jpeg', 0.88);
        return dataUrl.split(',')[1] || null;
      }
    }
    return null;
  };

  const captureAndSendFrame = (triggerAnalyze: boolean = false) => {
    const frameB64 = captureCurrentFrameBase64();
    if (frameB64) {
      wsService.send({
        type: triggerAnalyze ? 'analyze_camera' : 'camera_frame_sync',
        frame_base64: frameB64,
        live_detect: showLiveDetection
      });
    }
  };

  const handleDeviceChange = async (newDeviceId: string) => {
    setSelectedDeviceId(newDeviceId);
    localStorage.setItem('aegis_preferred_camera', newDeviceId);
    await startWebcam(newDeviceId);
  };

  const handleCycleCamera = async () => {
    if (availableDevices.length <= 1) return;
    const currentIndex = availableDevices.findIndex((d) => d.deviceId === selectedDeviceId);
    const nextIndex = (currentIndex + 1) % availableDevices.length;
    const nextDevice = availableDevices[nextIndex];
    if (nextDevice) {
      await handleDeviceChange(nextDevice.deviceId);
    }
  };

  const handleAnalyzeSurroundings = () => {
    setIsAnalyzing(true);
    const frameB64 = captureCurrentFrameBase64();
    if (frameB64) {
      wsService.send({
        type: 'analyze_camera',
        frame_base64: frameB64
      });
    }
    wsService.sendMessage('What do you see in front of the camera?');
    setTimeout(() => setIsAnalyzing(false), 4000);
  };

  const handleCheckPerson = () => {
    const frameB64 = captureCurrentFrameBase64();
    if (frameB64) {
      wsService.send({
        type: 'camera_frame_sync',
        frame_base64: frameB64
      });
    }
    wsService.sendMessage('Is there a person in front of me?');
  };

  const handleTargetQuery = (targetName: string) => {
    wsService.sendMessage(`What can you tell me about the ${targetName} in front of the camera?`);
  };

  const setVideoRef = useCallback((node: HTMLVideoElement | null) => {
    videoRef.current = node;
    if (node && streamRef.current) {
      node.srcObject = streamRef.current;
      node.onloadedmetadata = () => {
        if (node.videoWidth > 0 && node.videoHeight > 0) {
          setFrameAspectRatio(node.videoWidth / node.videoHeight);
        }
        node.play().catch((e) => console.warn('Play error:', e));
      };
    }
  }, []);

  // Futuristic category style mapping with themed borders, glows and badges
  const getObjectStyle = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('person') || n.includes('human') || n.includes('face')) {
      return {
        border: 'border-cyan-400',
        cornerBorder: 'border-cyan-300',
        bg: 'bg-cyan-950/90',
        tint: 'bg-cyan-500/10',
        text: 'text-cyan-300',
        badgeBorder: 'border-cyan-500/50',
        bar: 'bg-cyan-400',
        icon: '👤',
        categoryTag: 'HUMAN',
        glow: 'shadow-[0_0_20px_rgba(6,182,212,0.45)]'
      };
    }
    if (
      n.includes('phone') ||
      n.includes('mobile') ||
      n.includes('cell') ||
      n.includes('laptop') ||
      n.includes('remote') ||
      n.includes('keyboard') ||
      n.includes('mouse') ||
      n.includes('screen')
    ) {
      return {
        border: 'border-emerald-400',
        cornerBorder: 'border-emerald-300',
        bg: 'bg-emerald-950/90',
        tint: 'bg-emerald-500/10',
        text: 'text-emerald-300',
        badgeBorder: 'border-emerald-500/50',
        bar: 'bg-emerald-400',
        icon: n.includes('phone') || n.includes('mobile') || n.includes('cell') ? '📱' : n.includes('remote') ? '📺' : '💻',
        categoryTag: 'DEVICE',
        glow: 'shadow-[0_0_20px_rgba(16,185,129,0.45)]'
      };
    }
    if (n.includes('bottle') || n.includes('mug') || n.includes('cup') || n.includes('glass') || n.includes('drink')) {
      return {
        border: 'border-amber-400',
        cornerBorder: 'border-amber-300',
        bg: 'bg-amber-950/90',
        tint: 'bg-amber-500/10',
        text: 'text-amber-300',
        badgeBorder: 'border-amber-500/50',
        bar: 'bg-amber-400',
        icon: n.includes('bottle') ? '🍼' : '☕',
        categoryTag: 'CONTAINER',
        glow: 'shadow-[0_0_20px_rgba(245,158,11,0.45)]'
      };
    }
    if (n.includes('pillow') || n.includes('cushion') || n.includes('bed') || n.includes('sofa') || n.includes('chair')) {
      return {
        border: 'border-purple-400',
        cornerBorder: 'border-purple-300',
        bg: 'bg-purple-950/90',
        tint: 'bg-purple-500/10',
        text: 'text-purple-300',
        badgeBorder: 'border-purple-500/50',
        bar: 'bg-purple-400',
        icon: '🛏️',
        categoryTag: 'FURNITURE',
        glow: 'shadow-[0_0_20px_rgba(168,85,247,0.45)]'
      };
    }
    if (n.includes('painting') || n.includes('art') || n.includes('frame') || n.includes('poster')) {
      return {
        border: 'border-rose-400',
        cornerBorder: 'border-rose-300',
        bg: 'bg-rose-950/90',
        tint: 'bg-rose-500/10',
        text: 'text-rose-300',
        badgeBorder: 'border-rose-500/50',
        bar: 'bg-rose-400',
        icon: '🖼️',
        categoryTag: 'WALL ART',
        glow: 'shadow-[0_0_20px_rgba(244,63,94,0.45)]'
      };
    }
    return {
      border: 'border-sky-400',
      cornerBorder: 'border-sky-300',
      bg: 'bg-slate-900/95',
      tint: 'bg-sky-500/10',
      text: 'text-sky-300',
      badgeBorder: 'border-sky-500/50',
      bar: 'bg-sky-400',
      icon: '📦',
      categoryTag: 'OBJECT',
      glow: 'shadow-[0_0_20px_rgba(14,165,233,0.45)]'
    };
  };

  if (!isActive) {
    return null;
  }

  // MINIMIZED DOCK BAR
  if (isMinimized) {
    return (
      <div className="fixed right-6 bottom-20 z-30 flex items-center gap-3 px-4 py-2.5 rounded-2xl bg-slate-900/95 border border-cyan-500/40 shadow-2xl backdrop-blur-xl animate-fade-in text-slate-200">
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
        </span>
        <span className="text-xs font-bold tracking-wider text-slate-200 uppercase font-mono">Vision HUD</span>
        {liveBoxes.length > 0 && (
          <span className="text-[10px] bg-cyan-950/90 border border-cyan-500/40 text-cyan-300 px-2 py-0.5 rounded-full font-mono font-semibold">
            {liveBoxes.length} {liveBoxes.length === 1 ? 'Target' : 'Targets'}
          </span>
        )}
        <button
          onClick={() => setIsMinimized(false)}
          className="p-1 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition"
          title="Restore Vision Window"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          onClick={onToggleCamera}
          className="p-1 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
          title="Turn Off Camera"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    );
  }

  return (
    <>
      {/* Dark backdrop overlay when in full Theater/AR view */}
      {isExpanded && (
        <div
          onClick={() => setIsExpanded(false)}
          className="fixed inset-0 bg-slate-950/80 backdrop-blur-md z-40 animate-fade-in transition-opacity"
        />
      )}

      {/* Main Vision Dialog Container */}
      <div
        className={`transition-all duration-300 rounded-2xl border shadow-2xl overflow-hidden flex flex-col ${
          isExpanded
            ? 'fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-[960px] max-w-[95vw] max-h-[92vh] bg-slate-950/95 border-cyan-500/40 shadow-cyan-950/80'
            : 'fixed right-6 bottom-20 z-30 w-[540px] sm:w-[620px] md:w-[680px] max-w-[calc(100vw-1.5rem)] bg-slate-900/95 border-slate-700/80 shadow-slate-950/90'
        }`}
      >
        {/* Hidden Canvas for High-Res Frame Capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Top Header Bar */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-950/95 border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-cyan-500"></span>
            </span>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold tracking-wider text-slate-200 uppercase font-mono">
                AEGIS AR Vision
              </span>
              {isExpanded && (
                <span className="text-[10px] bg-indigo-950/80 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.5 rounded font-mono font-semibold">
                  Theater View
                </span>
              )}
            </div>

            {showLiveDetection && liveBoxes.length > 0 && (
              <span className="text-[11px] bg-emerald-950/90 border border-emerald-500/40 text-emerald-300 px-2 py-0.5 rounded-full font-mono font-bold flex items-center gap-1">
                <Crosshair className="w-3 h-3 text-emerald-400 animate-spin-slow" />
                <span>{liveBoxes.length} {liveBoxes.length === 1 ? 'Target Locked' : 'Targets Locked'}</span>
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            {/* Live Detection Overlay Toggle */}
            <button
              onClick={() => setShowLiveDetection(!showLiveDetection)}
              className={`px-2 py-1 rounded-lg text-xs font-mono font-semibold flex items-center gap-1 transition ${
                showLiveDetection
                  ? 'bg-emerald-950/70 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-900/60'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 border border-slate-700'
              }`}
              title={showLiveDetection ? 'Detection Overlays: ON' : 'Detection Overlays: OFF'}
            >
              {showLiveDetection ? <Eye className="w-3.5 h-3.5 text-emerald-400" /> : <EyeOff className="w-3.5 h-3.5" />}
              <span className="hidden sm:inline">{showLiveDetection ? 'HUD Active' : 'HUD Muted'}</span>
            </button>

            {/* Camera Selector / Switch Button */}
            {availableDevices.length > 1 && (
              <button
                onClick={handleCycleCamera}
                className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition"
                title="Switch Camera Device"
              >
                <SwitchCamera className="w-3.5 h-3.5" />
              </button>
            )}

            {/* Theater / Modal Expand Toggle */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition"
              title={isExpanded ? 'Exit Theater View' : 'Expand to Large Theater HUD'}
            >
              {isExpanded ? <Minimize2 className="w-4 h-4 text-cyan-400" /> : <Maximize2 className="w-4 h-4" />}
            </button>

            {/* Minimize to Dock Toggle (only in standard view) */}
            {!isExpanded && (
              <button
                onClick={() => setIsMinimized(true)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition"
                title="Minimize to Floating Bar"
              >
                <Minimize2 className="w-3.5 h-3.5" />
              </button>
            )}

            {/* Close Camera */}
            <button
              onClick={onToggleCamera}
              className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 border border-transparent hover:border-slate-700 transition"
              title="Close Camera"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-3.5 space-y-3 overflow-y-auto max-h-[calc(92vh-60px)]">
          {/* Top Control Bar: Device Selector + Diagnostic Info */}
          <div className="flex items-center gap-2">
            <div className="flex-1 flex items-center gap-2 px-3 py-1.5 bg-slate-950/90 rounded-xl border border-slate-800 text-[11px]">
              <Video className="w-3.5 h-3.5 text-cyan-400 flex-shrink-0" />
              <select
                value={selectedDeviceId}
                onChange={(e) => handleDeviceChange(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none w-full truncate text-[11px] font-medium cursor-pointer"
              >
                {availableDevices.length > 0 ? (
                  availableDevices.map((d) => (
                    <option key={d.deviceId} value={d.deviceId} className="bg-slate-900 text-slate-100 py-1">
                      {d.isInbuilt ? `✓ ${d.label} (Integrated)` : d.label}
                    </option>
                  ))
                ) : (
                  <option value="" className="bg-slate-900 text-slate-400">
                    Integrated Camera
                  </option>
                )}
              </select>
            </div>

            <button
              onClick={() => setShowTargetDetails(!showTargetDetails)}
              className={`px-2.5 py-1.5 rounded-xl border text-[11px] font-mono flex items-center gap-1.5 transition ${
                showTargetDetails
                  ? 'bg-cyan-950/60 border-cyan-500/40 text-cyan-300'
                  : 'bg-slate-950/90 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
              title="Toggle Detailed Spatial Tags"
            >
              <Layers className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{showTargetDetails ? 'Tags: On' : 'Tags: Off'}</span>
            </button>
          </div>

          {/* Video Preview Box with Cybernetic AR Bounding Overlays */}
          <div
            style={{ aspectRatio: `${frameAspectRatio}` }}
            className={`relative rounded-2xl overflow-hidden bg-black border border-slate-800 shadow-xl flex items-center justify-center w-full ${
              isExpanded ? 'max-h-[620px]' : 'max-h-[460px]'
            }`}
          >
            {/* Native HTML5 Video Stream */}
            <video
              ref={setVideoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-fill ${permissionState === 'granted' ? 'block' : 'hidden'}`}
            />

            {/* Cybernetic Scanlines Background Overlay */}
            <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%)] bg-[length:100%_4px] opacity-35" />

            {/* Top HUD Telemetry Corner Overlays */}
            <div className="absolute top-2.5 left-3 pointer-events-none z-10 flex items-center gap-2 text-[10px] font-mono text-cyan-400/80 bg-black/60 px-2 py-0.5 rounded backdrop-blur-sm border border-cyan-500/20">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
              <span>YOLOv5m • LIVE_TRACK</span>
            </div>

            {/* Live Real-Time Bounding Box Overlays */}
            {permissionState === 'granted' && showLiveDetection && (
              <div className="absolute inset-0 pointer-events-none overflow-hidden">
                {liveBoxes.map((box) => {
                  const style = getObjectStyle(box.name);
                  const pct = Math.round(box.confidence * 100);
                  const isHighlighted = activeTargetId === box.id;

                  // Calculate relative percentages matching frame exactly
                  const left = Math.max(0, Math.min(box.rel_x * 100, 96));
                  const top = Math.max(0, Math.min(box.rel_y * 100, 96));
                  const width = Math.min(box.rel_w * 100, 100 - left);
                  const height = Math.min(box.rel_h * 100, 100 - top);

                  // If box is near top of container, render badge inside box to prevent clipping
                  const badgePositionClass = top < 12 ? 'top-1 left-1' : '-top-7 left-0';

                  return (
                    <div
                      key={box.id}
                      className={`absolute border-2 ${style.border} ${style.glow} ${style.tint} rounded-xl transition-all duration-150 ${
                        isHighlighted ? 'ring-2 ring-white shadow-2xl scale-[1.01]' : ''
                      }`}
                      style={{
                        left: `${left}%`,
                        top: `${top}%`,
                        width: `${width}%`,
                        height: `${height}%`,
                        transition: 'all 160ms cubic-bezier(0.16, 1, 0.3, 1)'
                      }}
                    >
                      {/* High-Tech Cyberpunk Corner Brackets */}
                      <span className={`absolute -top-1 -left-1 w-3.5 h-3.5 border-t-2 border-l-2 ${style.cornerBorder}`} />
                      <span className={`absolute -top-1 -right-1 w-3.5 h-3.5 border-t-2 border-r-2 ${style.cornerBorder}`} />
                      <span className={`absolute -bottom-1 -left-1 w-3.5 h-3.5 border-b-2 border-l-2 ${style.cornerBorder}`} />
                      <span className={`absolute -bottom-1 -right-1 w-3.5 h-3.5 border-b-2 border-r-2 ${style.cornerBorder}`} />

                      {/* Center Targeting Reticle */}
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2.5 h-2.5 flex items-center justify-center opacity-60">
                        <div className={`w-1.5 h-1.5 rounded-full ${style.bar}`} />
                      </div>

                      {/* Floating Detection Badge */}
                      <div
                        className={`absolute ${badgePositionClass} z-20 flex items-center gap-1.5 px-2 py-0.5 rounded-lg ${style.bg} border ${style.badgeBorder} text-[11px] font-bold font-mono tracking-wide ${style.text} shadow-xl backdrop-blur-md whitespace-nowrap`}
                      >
                        <span className="text-xs">{style.icon}</span>
                        <span className="uppercase font-bold tracking-wider">{box.name}</span>
                        <span className="text-white font-mono text-[9px] bg-black/70 px-1.5 py-0.2 rounded font-bold">
                          {pct}%
                        </span>

                        {/* Optional Spatial Location Tag */}
                        {showTargetDetails && box.location && (
                          <span className="text-[9px] text-cyan-200 bg-cyan-950/80 border border-cyan-500/30 px-1 py-0.2 rounded uppercase font-semibold">
                            {box.location}
                          </span>
                        )}

                        {/* Mini Strength Meter Bar */}
                        <div className="w-5 h-1.5 bg-black/70 rounded-full overflow-hidden flex">
                          <div
                            className={`h-full ${style.bar} transition-all duration-200`}
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Permission Prompt Box if blocked */}
            {permissionState === 'denied' && (
              <div className="p-6 text-center space-y-3 bg-slate-950/90 rounded-2xl border border-rose-500/30 m-4">
                <AlertCircle className="w-8 h-8 text-rose-400 mx-auto animate-bounce" />
                <p className="text-sm text-slate-200 font-semibold">Camera Access Blocked or In Use</p>
                <p className="text-xs text-slate-400">Ensure browser camera permission is allowed and no other app is locking the camera.</p>
                <button
                  onClick={() => startWebcam()}
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-2 mx-auto transition shadow-lg"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry Camera Connection</span>
                </button>
              </div>
            )}

            {/* Connecting Camera Spinner */}
            {permissionState === 'pending' && (
              <div className="flex items-center gap-2.5 text-xs text-cyan-400 font-mono">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Synchronizing Neural Camera Stream...</span>
              </div>
            )}

            {/* Non-intrusive Analysis Status Pill */}
            {isAnalyzing && permissionState === 'granted' && (
              <div className="absolute top-3 left-1/2 -translate-x-1/2 bg-slate-900/95 border border-cyan-400/60 backdrop-blur-md px-4 py-1.5 rounded-full flex items-center gap-2 shadow-2xl animate-fade-in z-20">
                <Sparkles className="w-4 h-4 text-cyan-400 animate-spin" />
                <span className="text-xs font-bold text-cyan-200 font-mono">Analyzing visual scene...</span>
              </div>
            )}
          </div>

          {/* Interactive Live Target Matrix Strip */}
          {permissionState === 'granted' && liveBoxes.length > 0 && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[11px] text-slate-400 font-mono px-1">
                <span className="flex items-center gap-1 text-slate-300">
                  <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
                  <span>TRACKED TARGETS (Tap chip to ask AEGIS)</span>
                </span>
                <span className="text-cyan-400 font-semibold">{liveBoxes.length} detected</span>
              </div>

              <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-thin">
                {liveBoxes.map((box) => {
                  const style = getObjectStyle(box.name);
                  const pct = Math.round(box.confidence * 100);
                  return (
                    <button
                      key={box.id}
                      onClick={() => handleTargetQuery(box.name)}
                      onMouseEnter={() => setActiveTargetId(box.id)}
                      onMouseLeave={() => setActiveTargetId(null)}
                      className={`flex-shrink-0 flex items-center gap-1.5 px-2.5 py-1 rounded-xl ${style.bg} border ${style.badgeBorder} hover:border-white transition-all text-[11px] font-mono font-medium shadow-sm hover:scale-105 active:scale-95`}
                      title={`Click to ask AEGIS about this ${box.name}`}
                    >
                      <span>{style.icon}</span>
                      <span className="uppercase font-bold text-slate-100">{box.name}</span>
                      <span className="text-[10px] text-cyan-300 font-bold bg-black/60 px-1 py-0.2 rounded">
                        {pct}%
                      </span>
                      {box.location && (
                        <span className="text-[9px] text-slate-300 opacity-80">({box.location})</span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Quick Vision Action Buttons */}
          <div className="grid grid-cols-2 gap-2.5">
            <button
              onClick={handleAnalyzeSurroundings}
              disabled={isAnalyzing || permissionState !== 'granted'}
              className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-cyan-950/80 hover:bg-cyan-900/90 border border-cyan-500/40 text-cyan-300 text-xs font-bold tracking-wide transition shadow-lg active:scale-95 disabled:opacity-50 hover:shadow-cyan-900/30"
            >
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>What do you see?</span>
            </button>

            <button
              onClick={handleCheckPerson}
              disabled={permissionState !== 'granted'}
              className="flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-indigo-950/80 hover:bg-indigo-900/90 border border-indigo-500/40 text-indigo-300 text-xs font-bold tracking-wide transition shadow-lg active:scale-95 disabled:opacity-50 hover:shadow-indigo-900/30"
            >
              <UserCheck className="w-4 h-4 text-indigo-400" />
              <span>Person Check</span>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

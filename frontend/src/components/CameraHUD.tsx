import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Camera, Sparkles, UserCheck, X, Maximize2, Minimize2, Video, RefreshCw, AlertCircle, SwitchCamera, Scan, Eye, EyeOff } from 'lucide-react';
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

interface LiveDetectionBox {
  name: string;
  confidence: number;
  location?: string;
  spatial_relationship?: string;
  rel_x: number;
  rel_y: number;
  rel_w: number;
  rel_h: number;
}

export const CameraHUD: React.FC<CameraHUDProps> = ({
  isActive,
  isContinuous,
  onToggleCamera,
  onClose
}) => {
  const [isMinimized, setIsMinimized] = useState<boolean>(false);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [permissionState, setPermissionState] = useState<'granted' | 'prompt' | 'denied' | 'pending'>('pending');
  const [errorDetails, setErrorDetails] = useState<string>('');
  
  const [availableDevices, setAvailableDevices] = useState<VideoDevice[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>(() => {
    return localStorage.getItem('aegis_preferred_camera') || '';
  });

  // Live real-time detections and bounding boxes
  const [liveBoxes, setLiveBoxes] = useState<LiveDetectionBox[]>([]);
  const [showLiveDetection, setShowLiveDetection] = useState<boolean>(true);
  const [frameAspectRatio, setFrameAspectRatio] = useState<number>(4 / 3);

  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

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

    // Sort: Inbuilt first, then other real hardware cameras, then virtual/phone-link last
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

  // Subscribe to live WebSocket detections with dynamic aspect ratio sync
  useEffect(() => {
    const unsub = wsService.subscribe((data) => {
      if (data.type === 'live_detections') {
        if (data.frame_w && data.frame_h && data.frame_h > 0) {
          setFrameAspectRatio(data.frame_w / data.frame_h);
        }
        setLiveBoxes(data.boxes || []);
      }
    });
    return () => unsub();
  }, []);

  // Real-time frame transmission to backend (every 450ms for snappy live tracking)
  useEffect(() => {
    if (!isActive || permissionState !== 'granted') {
      setLiveBoxes([]);
      return;
    }

    const interval = setInterval(() => {
      captureAndSendFrame(false);
    }, 450);

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

  // Dynamic visual style mapper for detected objects & people
  const getObjectStyle = (name: string) => {
    const n = name.toLowerCase();
    if (n.includes('person') || n.includes('human') || n.includes('face')) {
      return {
        border: 'border-cyan-400',
        bg: 'bg-cyan-950/90',
        text: 'text-cyan-300',
        bar: 'bg-cyan-400',
        icon: '👤',
        glow: 'shadow-[0_0_15px_rgba(6,182,212,0.5)]'
      };
    }
    if (n.includes('phone') || n.includes('mobile') || n.includes('cell') || n.includes('laptop') || n.includes('remote') || n.includes('keyboard') || n.includes('mouse') || n.includes('screen')) {
      return {
        border: 'border-emerald-400',
        bg: 'bg-emerald-950/90',
        text: 'text-emerald-300',
        bar: 'bg-emerald-400',
        icon: n.includes('phone') || n.includes('mobile') || n.includes('cell') ? '📱' : n.includes('remote') ? '📺' : '💻',
        glow: 'shadow-[0_0_15px_rgba(16,185,129,0.5)]'
      };
    }
    if (n.includes('bottle') || n.includes('mug') || n.includes('cup') || n.includes('glass') || n.includes('flask') || n.includes('drink')) {
      return {
        border: 'border-amber-400',
        bg: 'bg-amber-950/90',
        text: 'text-amber-300',
        bar: 'bg-amber-400',
        icon: n.includes('bottle') ? '🍼' : '☕',
        glow: 'shadow-[0_0_15px_rgba(245,158,11,0.5)]'
      };
    }
    if (n.includes('pillow') || n.includes('cushion') || n.includes('bed') || n.includes('sofa') || n.includes('chair')) {
      return {
        border: 'border-purple-400',
        bg: 'bg-purple-950/90',
        text: 'text-purple-300',
        bar: 'bg-purple-400',
        icon: '🛏️',
        glow: 'shadow-[0_0_15px_rgba(168,85,247,0.5)]'
      };
    }
    if (n.includes('painting') || n.includes('art') || n.includes('frame') || n.includes('poster')) {
      return {
        border: 'border-rose-400',
        bg: 'bg-rose-950/90',
        text: 'text-rose-300',
        bar: 'bg-rose-400',
        icon: '🖼️',
        glow: 'shadow-[0_0_15px_rgba(244,63,94,0.5)]'
      };
    }
    return {
      border: 'border-blue-400',
      bg: 'bg-blue-950/90',
      text: 'text-blue-300',
      bar: 'bg-blue-400',
      icon: '📦',
      glow: 'shadow-[0_0_15px_rgba(59,130,246,0.5)]'
    };
  };

  if (!isActive) {
    return null;
  }

  return (
    <div
      className={`fixed right-6 bottom-24 z-30 transition-all duration-300 rounded-2xl glass-panel border border-slate-700/80 shadow-2xl shadow-slate-950/70 overflow-hidden ${
        isMinimized ? 'w-72 h-14' : 'w-80 sm:w-96'
      }`}
    >
      {/* Hidden Canvas for High-Res Frame Capture */}
      <canvas ref={canvasRef} className="hidden" />

      {/* Clean Top Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 bg-slate-900/95 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
          </span>
          <span className="text-xs font-bold tracking-wider text-slate-200 uppercase">Camera</span>
          {showLiveDetection && liveBoxes.length > 0 && (
            <span className="text-[10px] bg-emerald-950/90 border border-emerald-500/40 text-emerald-300 px-1.5 py-0.5 rounded font-mono font-semibold animate-pulse">
              {liveBoxes.length} {liveBoxes.length === 1 ? 'Target' : 'Targets'}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1">
          {/* Live Detection Toggle Button */}
          <button
            onClick={() => setShowLiveDetection(!showLiveDetection)}
            className={`p-1 rounded-md transition ${
              showLiveDetection
                ? 'text-emerald-400 hover:bg-emerald-950/60'
                : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800'
            }`}
            title={showLiveDetection ? 'Live Detection: ON' : 'Live Detection: OFF'}
          >
            {showLiveDetection ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
          </button>

          {availableDevices.length > 1 && (
            <button
              onClick={handleCycleCamera}
              className="p-1 rounded-md text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition"
              title="Switch Camera Device"
            >
              <SwitchCamera className="w-3.5 h-3.5" />
            </button>
          )}
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="p-1 rounded-md text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition"
            title={isMinimized ? "Expand" : "Minimize"}
          >
            {isMinimized ? <Maximize2 className="w-3.5 h-3.5" /> : <Minimize2 className="w-3.5 h-3.5" />}
          </button>
          <button
            onClick={onToggleCamera}
            className="p-1 rounded-md text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
            title="Turn Off Camera"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {!isMinimized && (
        <div className="p-3 space-y-2.5">
          {/* Camera Device Selector: Always accessible, prioritizes Integrated Camera */}
          <div className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-950/90 rounded-xl border border-slate-800 text-[11px]">
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

          {/* Live Video Preview Box with Live Bounding Boxes */}
          <div
            style={{ aspectRatio: `${frameAspectRatio}` }}
            className="relative rounded-xl overflow-hidden bg-black border border-slate-800 shadow-md flex items-center justify-center w-full max-h-[300px]"
          >
            {/* Native HTML5 Video Stream */}
            <video
              ref={setVideoRef}
              autoPlay
              playsInline
              muted
              className={`w-full h-full object-fill ${permissionState === 'granted' ? 'block' : 'hidden'}`}
            />

            {/* Live Real-Time Bounding Box Overlays */}
            {permissionState === 'granted' && showLiveDetection && (
              <div className="absolute inset-0 pointer-events-none overflow-hidden">
                {liveBoxes.map((box, idx) => {
                  const style = getObjectStyle(box.name);
                  const pct = Math.round(box.confidence * 100);

                  // Calculate relative percentages matching frame exactly
                  const left = Math.max(0, Math.min(box.rel_x * 100, 96));
                  const top = Math.max(0, Math.min(box.rel_y * 100, 96));
                  const width = Math.min(box.rel_w * 100, 100 - left);
                  const height = Math.min(box.rel_h * 100, 100 - top);

                  // If box is near top of container, render tag inside box to prevent clipping
                  const tagPositionClass = top < 10 ? 'top-1 left-1' : '-top-6 left-0';

                  return (
                    <div
                      key={`${box.name}-${idx}`}
                      className={`absolute border-2 ${style.border} ${style.glow} rounded-lg transition-all duration-150`}
                      style={{
                        left: `${left}%`,
                        top: `${top}%`,
                        width: `${width}%`,
                        height: `${height}%`
                      }}
                    >
                      {/* Floating Detection Badge with Strength Meter */}
                      <div
                        className={`absolute ${tagPositionClass} z-10 flex items-center gap-1.5 px-2 py-0.5 rounded-md ${style.bg} border ${style.border} text-[10px] font-bold font-mono tracking-wide ${style.text} shadow-md backdrop-blur-sm whitespace-nowrap`}
                      >
                        <span>{style.icon}</span>
                        <span className="uppercase">{box.name}</span>
                        <span className="text-white font-mono text-[9px] bg-black/60 px-1 py-0.2 rounded font-bold">
                          {pct}%
                        </span>
                        {/* Mini Strength Meter Bar */}
                        <div className="w-6 h-1.5 bg-black/60 rounded-full overflow-hidden flex">
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
              <div className="p-4 text-center space-y-2">
                <AlertCircle className="w-6 h-6 text-amber-400 mx-auto" />
                <p className="text-xs text-slate-300 font-medium">Camera access blocked or in use.</p>
                <button
                  onClick={() => startWebcam()}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold flex items-center gap-1.5 mx-auto transition shadow"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry Camera</span>
                </button>
              </div>
            )}

            {/* Loading state */}
            {permissionState === 'pending' && (
              <div className="flex items-center gap-2 text-xs text-cyan-400">
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Connecting camera...</span>
              </div>
            )}

            {/* Non-intrusive Analysis Status Pill */}
            {isAnalyzing && permissionState === 'granted' && (
              <div className="absolute top-2.5 left-1/2 -translate-x-1/2 bg-slate-900/90 border border-cyan-500/50 backdrop-blur-md px-3 py-1 rounded-full flex items-center gap-1.5 shadow-lg animate-fade-in z-10">
                <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-spin" />
                <span className="text-[11px] font-semibold text-cyan-200">Analyzing scene...</span>
              </div>
            )}
          </div>

          {/* Quick Vision Action Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={handleAnalyzeSurroundings}
              disabled={isAnalyzing || permissionState !== 'granted'}
              className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-cyan-950/70 hover:bg-cyan-900/80 border border-cyan-500/40 text-cyan-300 text-xs font-semibold tracking-wide transition shadow-sm active:scale-95 disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>What do you see?</span>
            </button>

            <button
              onClick={handleCheckPerson}
              disabled={permissionState !== 'granted'}
              className="flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-indigo-950/70 hover:bg-indigo-900/80 border border-indigo-500/40 text-indigo-300 text-xs font-semibold tracking-wide transition shadow-sm active:scale-95 disabled:opacity-50"
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Person Check</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

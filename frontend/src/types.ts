export type AssistantState =
  | 'IDLE'
  | 'LISTENING'
  | 'THINKING'
  | 'EXECUTING'
  | 'SPEAKING'
  | 'CAMERA_ACTIVE'
  | 'ERROR';

export interface FlightBookingData {
  origin: string;
  origin_code?: string;
  destination: string;
  dest_code?: string;
  date: string;
  iso_date?: string;
  site?: string;
  url?: string;
  awaiting_site?: boolean;
  awaiting_destination?: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tool?: string;
  verified?: boolean;
  action?: string;
  url?: string;
  booking_data?: FlightBookingData;
  timestamp: string;
  isVoice?: boolean;
}

export interface ReminderItem {
  id: number;
  text: string;
  time: string;
  raw_time?: string;
  is_active?: boolean;
}

export interface RoutineItem {
  id: number;
  action_type: string;
  target: string;
  time_of_day: string;
  frequency: number;
  auto_enabled: boolean;
}

export interface RoutineSuggestion {
  id: number;
  action_type: string;
  target: string;
  time_slot: string;
  frequency: number;
  message: string;
}

export interface MemoryItem {
  id?: number;
  key: string;
  value: string;
  category?: string;
}

export interface VisualMemoryItem {
  id: number;
  object: string;
  location_context: string;
  room: string;
  spatial_relationship?: string;
  confidence: number;
  last_seen: string;
  is_user_saved?: boolean;
}

export interface SystemStatus {
  app_name: string;
  version: string;
  clock: {
    time: string;
    raw_time: string;
    timezone: string;
    message: string;
  };
  date: {
    date: string;
    day: string;
    month: string;
    year: number;
    message: string;
  };
  system_info: {
    os: string;
    cpu_usage: string;
    ram_usage: string;
    battery: string;
    hostname: string;
    username: string;
  };
  camera_active: boolean;
  continuous_camera: boolean;
  model: string;
  has_api_key: boolean;
}

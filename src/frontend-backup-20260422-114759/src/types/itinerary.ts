export interface CandidatePoiData {
  id: string
  name: string
  tier: number
  category: string
  taste_tags: string[]
  highlight_note?: string
  permanent_features?: string[]
  walk_time_minutes?: number
  rating?: number | null
  latitude?: number
  longitude?: number
  district?: string | null
  region_key?: string | null
  cover_image_url?: string | null
  is_free?: boolean | null
  ticket_url?: string | null
  description?: string | null
  suggested_route?: string | null
  suggested_duration_minutes?: number | null
}

export interface CandidatePoiRequestPayload {
  destinations: string[]
  date_range?: [number, number] | number[] | null
  trip_days?: number
  styles: string[]
  crowd_preference?: string
  budget?: string
  extra_info?: string
  scenario_id?: string
  group?: string
}

export interface CandidatePoiResponseData {
  city: string
  trip_days: number
  user_input: string
  candidates: CandidatePoiData[]
}

export interface GenerateFromPoisPayload {
  user_input: string
  selected_pois: CandidatePoiData[]
  city: string
  trip_days: number
  scenario_id?: string
  group?: string
}

export interface POIVisitData {
  poi_id?: string
  time_slot: string
  name: string
  vibe_description: string
  highlight_note?: string
  walk_to_next_minutes?: number
  tier?: number
  latitude?: number  // POI coordinate from database
  longitude?: number // POI coordinate from database
  duration_minutes?: number  // 游玩时长（分钟）
}

export interface DayData {
  day_number: number
  theme: string
  pois: POIVisitData[]
  date?: string  // 日期（如"4月20日"）
  weather?: string  // 天气描述
  summary?: string  // 每日小结
}

export interface ItineraryData {
  title: string
  summary: string
  days: DayData[]
  total_walking_minutes: number
}

export interface ChangeItem {
  action: 'add' | 'replace' | 'delete'
  day_number: number
  position: number
  old_poi: POIVisitData | null
  new_poi: POIVisitData | null
}

export interface AdjustmentPreview {
  changes: ChangeItem[]
  updated_itinerary: ItineraryData
}

export interface FeedbackPayload {
  itinerary_id: string
  rating: '准' | '一般' | '不准'
  comment?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  text: string
}

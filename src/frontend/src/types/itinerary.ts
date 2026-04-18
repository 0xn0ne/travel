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
}

export interface DayData {
  day_number: number
  theme: string
  pois: POIVisitData[]
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

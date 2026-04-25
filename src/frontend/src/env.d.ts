/// <reference types="vite/client" />

interface AMapWindow {
  AMap: typeof AMap
}

declare var AMap: typeof AMap

interface AMap {
  Map: new (el: HTMLElement | string, opts?: Record<string, unknown>) => AMapMap
  MouseTool: new (map: AMapMap) => AMapMouseTool
  PlaceSearch: new (opts?: Record<string, unknown>) => AMapPlaceSearch
  CircleEditor: new (map: AMapMap, circle: AMapCircle) => AMapCircleEditor
  Icon: new (opts: { size: AMapSize; image: string; imageSize?: AMapSize }) => AMapIcon
  Size: new (w: number, h: number) => AMapSize
  Marker: new (opts: Record<string, unknown>) => AMapMarker
  Pixel: new (x: number, y: number) => AMapPixel
  LNGLat: new (lng: number, lat: number) => AMapLngLat
  Polyline: new (opts: Record<string, unknown>) => AMapPolyline
  Polygon: new (opts: Record<string, unknown>) => AMapPolygon
  CircleMarker: new (opts: Record<string, unknown>) => AMapCircleMarker
  PolyEditor: new (map: AMapMap) => unknown
}

interface AMapMap {
  add(overlay: AMapOverlay): void
  remove(overlay: AMapOverlay): void
  setFitView(overlays?: AMapOverlay[]): void
  destroy(): void
  setCenter(lnglat: AMapLngLat | [number, number]): void
  setStatus(opts: Record<string, boolean>): void
  on(event: string, handler: (e: any) => void): void
  off(event: string, handler: (e: any) => void): void
}

interface AMapOverlay {}
interface AMapMouseTool extends AMapOverlay {
  circle(opts: Record<string, unknown>): void
  on(event: string, handler: (e: AMapDrawEvent) => void): void
  close(): void
}
interface AMapDrawEvent {
  object: AMapCircle
}
interface AMapCircle extends AMapOverlay {
  getCenter(): AMapLngLat
  getRadius(): number
}
interface AMapLngLat {
  lng: number
  lat: number
}
interface AMapMarker extends AMapOverlay {
  on(event: string, handler: () => void): void
  setPosition(lnglat: AMapLngLat | [number, number]): void
}
interface AMapPlaceSearch extends AMapOverlay {}
interface AMapCircleEditor extends AMapOverlay {}
interface AMapIcon {}
interface AMapSize {}
interface AMapPixel {}
interface AMapPolyline extends AMapOverlay {
  setMap(map: AMapMap | null): void
}
interface AMapPolygon extends AMapOverlay {
  setMap(map: AMapMap | null): void
}
interface AMapCircleMarker extends AMapOverlay {
  setMap(map: AMapMap | null): void
}

interface Window {
  AMap: typeof AMap
}

import {osmTileProvider} from './streetMap';
export const streetTileProvider=osmTileProvider(import.meta.env.VITE_OSM_TILE_URL);

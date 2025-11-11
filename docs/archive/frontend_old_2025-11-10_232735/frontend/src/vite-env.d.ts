/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string;
  readonly VITE_ASSET_CDN_URL: string;
  readonly VITE_ENABLE_ANALYTICS: string;
  readonly VITE_ENABLE_DEBUG: string;
  readonly VITE_TARGET_FPS: string;
  readonly VITE_MOBILE_TARGET_FPS: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

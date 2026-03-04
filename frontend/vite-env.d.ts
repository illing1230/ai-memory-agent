/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TEST_PASSWORD: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

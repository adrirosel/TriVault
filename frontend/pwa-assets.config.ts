import { defineConfig, minimal2023Preset } from '@vite-pwa/assets-generator/config'

// Regenerate icons with: npx pwa-assets-generator
export default defineConfig({
  preset: {
    ...minimal2023Preset,
    maskable: { ...minimal2023Preset.maskable, resizeOptions: { background: '#09090B' } },
    apple: { ...minimal2023Preset.apple, resizeOptions: { background: '#09090B' } },
  },
  images: ['public/app-icon.svg'],
})

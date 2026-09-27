import { defineConfig, mergeConfig } from 'vitest/config'
import viteConfig from './vite.config'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/test/setup.ts'],
      include: ['src/**/*.{spec,test}.ts'],
      coverage: {
        provider: 'v8',
        reporter: ['text', 'html'],
        include: ['src/**/*.{ts,vue}'],
        exclude: [
          'src/**/*.{spec,test}.ts',
          'src/test/**',
          'src/api/types.ts',
          'src/main.ts',
          'src/**/*.d.ts',
        ],
      },
    },
  }),
)
